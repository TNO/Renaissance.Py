# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the migration-type-recipes.py CLI script (src/rejuvenation).

The script's filename is hyphenated (not a legal dotted module path), so it's loaded via
importlib.util.spec_from_file_location instead of a normal import - see _load_script().
"""

import importlib.util
import textwrap
from pathlib import Path
from types import ModuleType

import pytest
from hamcrest import assert_that, contains_string, equal_to, not_
from hamcrest.core.matcher import Matcher

from renaissance.recipes.type_var_domain import DOCS_BASE_URL, UNSAFE_RULES, UnsafeReason

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "src" / "rejuvenation" / "migration-type-recipes.py"


def _load_script() -> ModuleType:
    """Import migration-type-recipes.py as a module despite its hyphenated filename."""
    spec = importlib.util.spec_from_file_location("migration_type_recipes", _SCRIPT_PATH)
    if spec is None or spec.loader is None:
        message = f"could not load {_SCRIPT_PATH} as a module"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migration = _load_script()


LEGACY_TYPEVAR_SOURCE = textwrap.dedent("""\
    from typing import TypeVar

    T = TypeVar("T")


    def identity(x: T) -> T:
        return x
    """)

UNSAFE_TYPEVAR_SOURCE = textwrap.dedent("""\
    from typing import TypeVar

    T = TypeVar("T")

    __all__ = ["T"]


    def identity(x: T) -> T:
        return x
    """)


class TestProcessFile:
    """process_file: writes changes for real, and isolates per-file errors."""

    @pytest.mark.parametrize(
        ("source", "imported_elsewhere", "expected_reason"),
        [
            pytest.param(UNSAFE_TYPEVAR_SOURCE, frozenset[str](), UnsafeReason.DECLARED_TYPEVAR_EXPORTED, id="exported-via-dunder-all"),
            pytest.param(LEGACY_TYPEVAR_SOURCE, frozenset({"T"}), UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT, id="imported-elsewhere"),
        ],
    )
    def test_converts_function_but_keeps_a_declaration_others_rely_on(
        self, tmp_path: Path, source: str, imported_elsewhere: frozenset[str], expected_reason: UnsafeReason
    ) -> None:
        """The function is converted on disk, the declaration stays, and the report says why it stayed."""
        target = tmp_path / "mod.py"
        target.write_text(source, encoding="utf-8")

        report = migration.process_file(target, min_python=(3, 12), project_root=tmp_path, project_wide_imported_names=imported_elsewhere)

        assert_that(migration.has_fixed(report), equal_to(obj=True))
        assert_that(report.reasons, not_(None))
        assert_that((report.reasons or {})["orphaned"], equal_to({"T": expected_reason}))
        written = target.read_text(encoding="utf-8")
        assert_that(written, contains_string("def identity[T](x: T) -> T:"))
        assert_that(written, contains_string('T = TypeVar("T")'))

    def test_syntax_error_reported_as_error_not_raised(self, tmp_path: Path) -> None:
        """A file that fails to parse is reported on FileReport.error, not raised."""
        target = tmp_path / "broken.py"
        target.write_text("def broken(:\n", encoding="utf-8")

        report = migration.process_file(target, min_python=(3, 12), project_root=tmp_path, project_wide_imported_names=frozenset[str]())

        assert_that(report.error, not_(None))
        assert_that(report.result, equal_to(None))


class TestRuffImportCleanup:
    """main(): the ruff F401 batch step actually drops now-unused imports end to end."""

    @pytest.mark.parametrize(
        ("extra_args", "import_matcher", "report_matcher"),
        [
            pytest.param(
                [],
                not_(contains_string("TypeVar")),
                contains_string("cleaned up via `ruff"),
                id="default-drops-import",
            ),
            pytest.param(
                ["--no-ruff"],
                contains_string("from typing import TypeVar"),
                not_(contains_string("cleaned up via `ruff")),
                id="no-ruff-keeps-import",
            ),
        ],
    )
    def test_unused_typevar_import_cleanup(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        extra_args: list[str],
        import_matcher: Matcher[str],
        report_matcher: Matcher[str],
    ) -> None:
        """The redundant TypeVar import is dropped, and the report says so, unless --no-ruff; conversion runs either way."""
        target = tmp_path / "mod.py"
        target.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")

        exit_code = migration.main([str(target), "--py", "3.12", *extra_args])

        assert_that(exit_code, equal_to(0))
        written = target.read_text(encoding="utf-8")
        assert_that(written, contains_string("def identity[T]"))
        assert_that(written, import_matcher)
        assert_that(capsys.readouterr().out, report_matcher)

    def test_localized_imports_are_merged_with_existing_ones(self, tmp_path: Path) -> None:
        """The localized TypeVar's import joins the file's own `typing` import; Python < 3.12 only localizes."""
        (tmp_path / "xarray_types.py").write_text(
            'from typing import TypeVar\n\nJoinOptions = str\nAlignable = int\nT = TypeVar("T")\n',
            encoding="utf-8",
        )
        target = tmp_path / "use.py"
        target.write_text(
            textwrap.dedent("""\
                from typing import Any
                from xarray_types import JoinOptions
                from xarray_types import T
                from xarray_types import Alignable


                def pick(x: T, how: JoinOptions, other: Alignable) -> Any:
                    return x
                """),
            encoding="utf-8",
        )

        exit_code = migration.main([str(target), "--py", "3.11"])

        assert_that(exit_code, equal_to(0))
        lines = target.read_text(encoding="utf-8").splitlines()
        for import_line in ["from typing import Any, TypeVar", "from xarray_types import Alignable, JoinOptions"]:
            assert_that(lines.count(import_line), equal_to(1), import_line)

    def test_unmodified_sibling_file_is_left_untouched(self, tmp_path: Path) -> None:
        """A sibling file with no TypeVar usage - and its own genuinely-unused import - survives main() byte-for-byte."""
        (tmp_path / "mod.py").write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        sibling = tmp_path / "sibling.py"
        sibling_source = textwrap.dedent("""\
            import os


            def greet() -> str:
                return "hi"
            """)
        sibling.write_text(sibling_source, encoding="utf-8")

        exit_code = migration.main([str(tmp_path), "--py", "3.12"])

        assert_that(exit_code, equal_to(0))
        assert_that(sibling.read_text(encoding="utf-8"), equal_to(sibling_source))


class TestConsoleReportNeedsReviewSection:
    """main(): what the NEEDS MANUAL REVIEW section lists per file."""

    def test_names_come_with_their_reason_under_one_shared_documentation_link(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Each name is listed with its reason in words; the documentation is linked once, without per-name anchors."""
        target = tmp_path / "mod.py"
        target.write_text(UNSAFE_TYPEVAR_SOURCE, encoding="utf-8")

        migration.main([str(target), "--py", "3.12"])

        output = capsys.readouterr().out
        assert_that(output.count(DOCS_BASE_URL), equal_to(1))
        assert_that(output, not_(contains_string("#feature-")))
        assert_that(output, contains_string("    T: exported via __all__\n"))
        assert_that(output, not_(contains_string("    orphaned:")))

    def test_name_converted_in_functions_but_still_used_by_a_generic_class_is_in_both_sections(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A name converted in some functions that a generic class still uses is listed as modified and as needing review."""
        target = tmp_path / "mod.py"
        target.write_text(
            textwrap.dedent("""\
                from typing import Generic, TypeVar

                T = TypeVar("T")


                def first(items: list[T]) -> T:
                    return items[0]


                class Box(Generic[T]):
                    def get(self, x: T) -> T:
                        return x
                """),
            encoding="utf-8",
        )

        migration.main([str(target), "--py", "3.12", "--no-ruff"])

        output = capsys.readouterr().out
        modified, needs_review = output.split("NEEDS MANUAL REVIEW (")
        assert_that(output, contains_string("1 modified, 1 need manual review"))
        assert_that(modified, contains_string("    T: converted to PEP 695 in functions\n"))
        assert_that(needs_review, contains_string("    T: only used inside a class that is generic over it\n"))


class TestConsoleReportModifiedSection:
    """main(): what the MODIFIED section lists per file."""

    def test_converted_name_is_not_listed_again_as_removed(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """A converted name is listed once; only declarations removed without a conversion are listed as removed."""
        target = tmp_path / "mod.py"
        target.write_text(
            textwrap.dedent("""\
                from typing import TypeVar

                T = TypeVar("T")
                U = TypeVar("U")


                def f(x: T) -> T:
                    return x


                def g[U](y: U) -> U:
                    return y
                """),
            encoding="utf-8",
        )

        migration.main([str(target), "--py", "3.12", "--no-ruff"])

        output = capsys.readouterr().out
        assert_that(output, contains_string("    T: converted to PEP 695 in functions\n"))
        assert_that(output, not_(contains_string("    T: unused declaration removed")))
        assert_that(output, contains_string("    U: unused declaration removed\n"))


def _table_rows(output: str, first_header: str) -> list[list[str]]:
    """Return the data rows, as stripped cells, of the printed Markdown table whose header starts with first_header."""
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in output.splitlines() if line.startswith("|")]
    start = next(index for index, row in enumerate(rows) if row[0] == first_header)
    table: list[list[str]] = []
    for row in rows[start + 2 :]:
        if row[0] in {"Kind", "Reason"}:
            break
        table.append(row)
    return table


class TestSummaryTables:
    """main(): the summary tables at the top of the printed report."""

    def test_counts_per_kind_and_reasons_by_frequency(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """A name counts once per file, needs review if it has a reason, errored files are skipped, reasons are ranked."""
        (tmp_path / "fixed.py").write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        (tmp_path / "exported_1.py").write_text(UNSAFE_TYPEVAR_SOURCE, encoding="utf-8")
        (tmp_path / "exported_2.py").write_text(UNSAFE_TYPEVAR_SOURCE, encoding="utf-8")
        (tmp_path / "bound_paramspec.py").write_text(
            textwrap.dedent("""\
                from collections.abc import Callable
                from typing import ParamSpec

                P = ParamSpec("P", bound=int)


                def wrap(f: Callable[P, int]) -> Callable[P, int]:
                    return f
                """),
            encoding="utf-8",
        )
        (tmp_path / "broken.py").write_text("def broken(:\n", encoding="utf-8")

        migration.main([str(tmp_path), "--py", "3.12", "--no-ruff"])

        output = capsys.readouterr().out
        assert_that(
            _table_rows(output, "Kind"),
            equal_to([["TypeVar", "3", "1", "2"], ["ParamSpec", "1", "0", "1"], ["TypeVarTuple", "0", "0", "0"]]),
        )
        assert_that(
            _table_rows(output, "Reason"),
            equal_to(
                [
                    [UNSAFE_RULES[UnsafeReason.DECLARED_TYPEVAR_EXPORTED].message, "2"],
                    [UNSAFE_RULES[UnsafeReason.NO_PEP695_EQUIVALENT].message, "1"],
                ],
            ),
        )


class TestPerFileProgressFeedback:
    """main(): prints a per-file progress line as each file is checked."""

    def test_progress_line_path_has_no_parent_segments(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """A target containing `..` is normalized before its files are reported."""
        good = tmp_path / "good.py"
        good.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        (tmp_path / "sub").mkdir()

        migration.main([str(tmp_path / "sub" / ".."), "--py", "3.12"])

        output = capsys.readouterr().out
        assert_that(output, contains_string(f"File {good} checked."))
        assert_that(output, not_(contains_string("..")))


class TestMainBatchErrorIsolation:
    """main(): one bad file in a batch must not abort processing of the rest."""

    def test_one_bad_file_does_not_abort_the_batch(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A batch with one broken file still checks and converts the good file, and exits with code 3."""
        good = tmp_path / "good.py"
        good.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        broken = tmp_path / "broken.py"
        broken.write_text("def broken(:\n", encoding="utf-8")

        exit_code = migration.main([str(tmp_path), "--py", "3.12"])

        assert_that(exit_code, equal_to(3))
        output = capsys.readouterr().out
        assert_that(output, contains_string(f"File {good} checked."))
        assert_that(output, contains_string(f"File {broken} checked."))
        assert_that(good.read_text(encoding="utf-8"), contains_string("def identity[T]"))


class TestMainProjectWideImportSafety:
    """main(): a TypeVar imported by another file in the batch is localized there and kept at its origin."""

    def test_consumer_is_localized_and_origin_declaration_survives(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """The importing file gets a PEP 695 local TypeVar, and the origin declaration is not removed."""
        import_line = "from pkg.typing_mod import T"
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "typing_mod.py").write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        consumer = pkg / "client.py"
        consumer.write_text(f"{import_line}\n\ndef use(x: T) -> T:\n    return x\n", encoding="utf-8")
        (pkg / "unused.py").write_text(f"{import_line}\n", encoding="utf-8")

        exit_code = migration.main([str(tmp_path), "--py", "3.12"])

        assert_that(exit_code, equal_to(0))
        consumer_text = consumer.read_text(encoding="utf-8")
        assert_that(consumer_text, contains_string("def use[T](x: T) -> T:"))
        assert_that(consumer_text, not_(contains_string(import_line)))
        assert_that(capsys.readouterr().out, contains_string("    T: unused declaration removed\n"))
        assert_that((pkg / "typing_mod.py").read_text(encoding="utf-8"), contains_string('T = TypeVar("T")'))

    @pytest.mark.parametrize("target_arg", [pytest.param(".", id="dot"), pytest.param("pkg", id="subdirectory")])
    def test_origin_declaration_survives_with_relative_target(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        target_arg: str,
    ) -> None:
        """A relative target path still protects a declaration imported by another file in the batch."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "typing_mod.py").write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        (pkg / "client.py").write_text("from .typing_mod import T\n\ndef use(x: T) -> T:\n    return x\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        exit_code = migration.main([target_arg, "--py", "3.12"])

        assert_that(exit_code, equal_to(0))
        assert_that((pkg / "typing_mod.py").read_text(encoding="utf-8"), contains_string('T = TypeVar("T")'))
        assert_that((pkg / "client.py").read_text(encoding="utf-8"), contains_string("def use[T](x: T) -> T:"))


class TestPyVersionFlag:
    """main(): the required --py flag alone sets the target's minimum Python version."""

    @pytest.mark.parametrize(
        ("py_version", "expected", "unexpected"),
        [
            pytest.param("3.11", 'T = TypeVar("T")', "def identity[", id="3.11-gated"),
            pytest.param("3.12", "def identity[T]", 'T = TypeVar("T")', id="3.12-converted"),
        ],
    )
    def test_py_flag_gates_rewrites(self, tmp_path: Path, py_version: str, expected: str, unexpected: str) -> None:
        """--py decides whether the PEP 695 rewrite runs."""
        target = tmp_path / "mod.py"
        target.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")

        exit_code = migration.main([str(target), "--py", py_version])

        assert_that(exit_code, equal_to(0))
        written = target.read_text(encoding="utf-8")
        assert_that(written, contains_string(expected))
        assert_that(written, not_(contains_string(unexpected)))

    @pytest.mark.parametrize(
        ("bad_args", "expected_error"),
        [
            pytest.param([], "the following arguments are required: --py", id="flag-missing"),
            pytest.param(["--py", "3.x"], "expected MAJOR.MINOR (e.g. 3.12), got '3.x'", id="non-numeric"),
        ],
    )
    def test_bad_version_arguments_are_usage_errors(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        bad_args: list[str],
        expected_error: str,
    ) -> None:
        """A missing or malformed --py flag exits with code 2 and an error saying what is wrong with it."""
        target = tmp_path / "mod.py"
        target.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")

        with pytest.raises(SystemExit) as excinfo:
            migration.main([str(target), *bad_args])

        assert_that(excinfo.value.code, equal_to(2))
        assert_that(capsys.readouterr().err, contains_string(expected_error))

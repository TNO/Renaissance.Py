"""Tests for the migration-type-recipes.py CLI script (src/rejuvenation).

The script's filename is hyphenated (not a legal dotted module path), so it's loaded via
importlib.util.spec_from_file_location instead of a normal import - see _load_script().
"""

import importlib.util
import textwrap
from pathlib import Path
from types import ModuleType

import pytest
from hamcrest import assert_that, contains_string, equal_to, is_, is_not
from hamcrest.core.matcher import Matcher

from renaissance.recipes.type_var_domain import UnsafeReason, doc_link

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
            pytest.param(UNSAFE_TYPEVAR_SOURCE, frozenset(), UnsafeReason.DECLARED_TYPEVAR_EXPORTED, id="exported-via-dunder-all"),
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

        assert_that(migration.has_fixed(report), is_(True))
        assert_that(report.reasons, is_not(None))
        assert_that((report.reasons or {})["orphaned"], equal_to({"T": expected_reason}))
        written = target.read_text(encoding="utf-8")
        assert_that(written, contains_string("def identity[T](x: T) -> T:"))
        assert_that(written, contains_string('T = TypeVar("T")'))

    def test_syntax_error_reported_as_error_not_raised(self, tmp_path: Path) -> None:
        """A file that fails to parse is reported on FileReport.error, not raised."""
        target = tmp_path / "broken.py"
        target.write_text("def broken(:\n", encoding="utf-8")

        report = migration.process_file(target, min_python=(3, 12), project_root=tmp_path, project_wide_imported_names=frozenset())

        assert_that(report.error, is_not(None))
        assert_that(report.result, is_(None))


class TestRuffImportCleanup:
    """main(): the ruff F401 batch step actually drops now-unused imports end to end."""

    @pytest.mark.parametrize(
        ("extra_args", "import_matcher", "report_matcher"),
        [
            pytest.param(
                [],
                is_not(contains_string("TypeVar")),
                contains_string("cleaned up via `ruff"),
                id="default-drops-import",
            ),
            pytest.param(
                ["--no-ruff"],
                contains_string("from typing import TypeVar"),
                is_not(contains_string("cleaned up via `ruff")),
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


class TestConsoleReportDocLinks:
    """main(): each unsafe name printed under NEEDS MANUAL REVIEW links to its documented rule."""

    def test_needs_manual_review_includes_doc_link_for_the_specific_reason(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The report links a __all__-exported TypeVar to the DECLARED_TYPEVAR_EXPORTED rule."""
        target = tmp_path / "mod.py"
        target.write_text(UNSAFE_TYPEVAR_SOURCE, encoding="utf-8")

        migration.main([str(target), "--py", "3.12"])

        output = capsys.readouterr().out
        assert_that(output, contains_string(doc_link(UnsafeReason.DECLARED_TYPEVAR_EXPORTED)))


class TestConsoleReportModifiedSection:
    """main(): what the MODIFIED section lists per file."""

    def test_converted_name_is_not_listed_again_as_orphaned(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """A converted name is listed once; only declarations removed without a conversion appear under orphaned."""
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
        assert_that(output, contains_string("    converted: T\n"))
        assert_that(output, contains_string("    orphaned: U\n"))


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
        assert_that(output, is_not(contains_string("..")))


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

    @pytest.mark.parametrize(
        ("consumer_rel", "import_line"),
        [
            pytest.param("pkg/client.py", "from pkg.typing_mod import T", id="absolute-dotted"),
            pytest.param("pkg/client.py", "from .typing_mod import T", id="relative"),
            pytest.param("other/client.py", "from pkg.typing_mod import T", id="absolute-other-directory"),
        ],
    )
    def test_consumer_is_localized_and_origin_declaration_survives(
        self,
        tmp_path: Path,
        consumer_rel: str,
        import_line: str,
    ) -> None:
        """The importing file gets a PEP 695 local TypeVar, and the origin declaration is not removed."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "typing_mod.py").write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        consumer = tmp_path / consumer_rel
        consumer.parent.mkdir(exist_ok=True)
        consumer.write_text(f"{import_line}\n\ndef use(x: T) -> T:\n    return x\n", encoding="utf-8")

        exit_code = migration.main([str(tmp_path), "--py", "3.12"])

        assert_that(exit_code, equal_to(0))
        consumer_text = consumer.read_text(encoding="utf-8")
        assert_that(consumer_text, contains_string("def use[T](x: T) -> T:"))
        assert_that(consumer_text, is_not(contains_string(import_line)))
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

    def test_origin_declaration_survives_module_attribute_access(self, tmp_path: Path) -> None:
        """A TypeVar accessed as a module attribute by another file is kept at its origin."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "typing_mod.py").write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        (pkg / "client.py").write_text("import pkg.typing_mod\n\ndef use(x: pkg.typing_mod.T) -> None: ...\n", encoding="utf-8")

        exit_code = migration.main([str(tmp_path), "--py", "3.12"])

        assert_that(exit_code, equal_to(0))
        assert_that((pkg / "typing_mod.py").read_text(encoding="utf-8"), contains_string('T = TypeVar("T")'))


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
        assert_that(written, is_not(contains_string(unexpected)))

    @pytest.mark.parametrize(
        ("bad_args", "expected_error"),
        [
            pytest.param([], "the following arguments are required: --py", id="flag-missing"),
            pytest.param(["--py", "3"], "expected MAJOR.MINOR (e.g. 3.12), got '3'", id="missing-minor"),
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

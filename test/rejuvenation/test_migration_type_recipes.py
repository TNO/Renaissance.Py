"""Tests for the migration-type-recipes.py CLI script (src/rejuvenation).

The script's filename is hyphenated (not a legal dotted module path), so it's loaded via
importlib.util.spec_from_file_location instead of a normal import - see _load_script().
"""

import importlib.util
import textwrap
from pathlib import Path
from types import ModuleType  # noqa: TC003

import pytest
from hamcrest import assert_that, contains_string, equal_to, is_, is_not

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

TYPEVARTUPLE_SOURCE = textwrap.dedent("""\
    from typing import TypeVarTuple, Unpack

    Ts = TypeVarTuple("Ts")


    def foo(*args: Unpack[Ts]) -> None:
        pass
    """)


class TestDiscoverFiles:
    """discover_files: recursive .py discovery with noise-directory exclusion."""

    def test_finds_nested_py_files(self, tmp_path: Path) -> None:
        """Nested .py files under ordinary directories are all found."""
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "a.py").write_text("x = 1\n")
        (tmp_path / "pkg" / "b.py").write_text("y = 2\n")

        result = migration.discover_files(tmp_path)

        assert_that([p.name for p in result], equal_to(["a.py", "b.py"]))

    @pytest.mark.parametrize("excluded_dir", [".git", "__pycache__", ".venv", "venv"])
    def test_excludes_known_noise_dirs(self, tmp_path: Path, excluded_dir: str) -> None:
        """A .py file under a known noise directory (.git, __pycache__, venvs) is skipped."""
        noise_dir = tmp_path / excluded_dir
        noise_dir.mkdir()
        (noise_dir / "ignored.py").write_text("x = 1\n")
        (tmp_path / "kept.py").write_text("y = 2\n")

        result = migration.discover_files(tmp_path)

        assert_that([p.name for p in result], equal_to(["kept.py"]))

    def test_single_file_returned_as_is(self, tmp_path: Path) -> None:
        """A single .py file path (not a directory) is returned as a one-item list."""
        target = tmp_path / "solo.py"
        target.write_text("x = 1\n")

        result = migration.discover_files(target)

        assert_that(result, equal_to([target]))


class TestClassification:
    """has_fixed/has_unsafe/is_clean: classification predicates over a FileReport."""

    @pytest.mark.parametrize(
        ("result", "expected"),
        [
            ({"cross_file": {}, "converted": {"T": "fixed"}, "orphaned": {}}, (True, False, False)),
            ({"cross_file": {}, "converted": {"T": "unsafe"}, "orphaned": {}}, (False, True, False)),
            (
                {"cross_file": {}, "converted": {"T": "fixed", "U": "unsafe"}, "orphaned": {}},
                (True, True, False),
            ),
            ({"cross_file": {}, "converted": {}, "orphaned": {}}, (False, False, True)),
        ],
    )
    def test_predicates(
        self,
        result: dict[str, dict[str, str]],
        expected: tuple[bool, bool, bool],
    ) -> None:
        """Each predicate matches the expected (fixed, unsafe, clean) reading of `result`."""
        expected_fixed, expected_unsafe, expected_clean = expected
        report = migration.FileReport(path=Path("x.py"), result=result, error=None)

        assert_that(migration.has_fixed(report), is_(expected_fixed))
        assert_that(migration.has_unsafe(report), is_(expected_unsafe))
        assert_that(migration.is_clean(report), is_(expected_clean))

    def test_error_report_is_neither_fixed_unsafe_nor_clean(self) -> None:
        """A report with no result (an error occurred) is False for every predicate."""
        report = migration.FileReport(path=Path("x.py"), result=None, error="boom")

        assert_that(migration.has_fixed(report), is_(False))
        assert_that(migration.has_unsafe(report), is_(False))
        assert_that(migration.is_clean(report), is_(False))


class TestProcessFile:
    """process_file: writes changes for real, and isolates per-file errors."""

    def test_writes_migrated_content_to_disk(self, tmp_path: Path) -> None:
        """process_file() actually writes the PEP 695-converted content to disk."""
        target = tmp_path / "mod.py"
        target.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")

        report = migration.process_file(target, min_python=(3, 12))

        assert_that(migration.has_fixed(report), is_(True))
        assert_that(target.read_text(encoding="utf-8"), contains_string("def identity[T]"))

    def test_unsafe_typevar_reported_but_not_written(self, tmp_path: Path) -> None:
        """A TypeVar exported via __all__ is reported unsafe and the file is left untouched."""
        target = tmp_path / "mod.py"
        target.write_text(UNSAFE_TYPEVAR_SOURCE, encoding="utf-8")
        original = target.read_text(encoding="utf-8")

        report = migration.process_file(target, min_python=(3, 12))

        assert_that(migration.has_unsafe(report), is_(True))
        assert_that(target.read_text(encoding="utf-8"), equal_to(original))

    def test_syntax_error_reported_as_error_not_raised(self, tmp_path: Path) -> None:
        """A file that fails to parse is reported on FileReport.error, not raised."""
        target = tmp_path / "broken.py"
        target.write_text("def broken(:\n", encoding="utf-8")

        report = migration.process_file(target, min_python=(3, 12))

        assert_that(report.error, is_not(None))
        assert_that(report.result, is_(None))

    def test_composes_typevarcheck_and_typevartuplecheck(self, tmp_path: Path) -> None:
        """TypeVarCheck's [*Ts] bracket and TypeVarTupleCheck's Unpack[Ts]->*Ts compose in one pass."""
        target = tmp_path / "mod.py"
        target.write_text(TYPEVARTUPLE_SOURCE, encoding="utf-8")

        report = migration.process_file(target, min_python=(3, 12))

        assert_that(migration.has_fixed(report), is_(True))
        output = target.read_text(encoding="utf-8")
        assert_that(output, contains_string("def foo[*Ts](*args: *Ts) -> None:"))
        assert_that(output, is_not(contains_string("Unpack[Ts]")))
        # process_file() alone doesn't run the ruff import-cleanup pass (that's main()'s job) -
        # both now-unused names are still present in the import at this layer.
        assert_that(output, contains_string("from typing import TypeVarTuple, Unpack"))


class TestRuffImportCleanup:
    """main(): the ruff F401 batch step actually drops now-unused imports end to end."""

    def test_unused_typevar_import_is_dropped(self, tmp_path: Path) -> None:
        """A TypeVar import made redundant by conversion is gone from disk after main() runs."""
        target = tmp_path / "mod.py"
        target.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")

        exit_code = migration.main([str(target), "--min-python", "3.12"])

        assert_that(exit_code, equal_to(0))
        written = target.read_text(encoding="utf-8")
        assert_that(written, contains_string("def identity[T]"))
        assert_that(written, is_not(contains_string("TypeVar")))

    def test_unrelated_import_survives_cleanup(self, tmp_path: Path) -> None:
        """An Unpack import still needed for an unrelated PEP 692 usage survives the ruff pass."""
        target = tmp_path / "mod.py"
        target.write_text(
            textwrap.dedent("""\
                from typing import TypeVarTuple, Unpack
                from mymodule import Kwargs

                Ts = TypeVarTuple("Ts")


                def foo(*args: Unpack[Ts], **kwargs: Unpack[Kwargs]) -> None:
                    pass
                """),
            encoding="utf-8",
        )

        exit_code = migration.main([str(target), "--min-python", "3.12"])

        assert_that(exit_code, equal_to(0))
        written = target.read_text(encoding="utf-8")
        assert_that(written, contains_string("*args: *Ts"))
        assert_that(written, contains_string("from typing import Unpack"))
        assert_that(written, is_not(contains_string("TypeVarTuple")))
        assert_that(written, contains_string("**kwargs: Unpack[Kwargs]"))

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

        exit_code = migration.main([str(tmp_path), "--min-python", "3.12"])

        assert_that(exit_code, equal_to(0))
        assert_that(sibling.read_text(encoding="utf-8"), equal_to(sibling_source))


class TestMainBatchErrorIsolation:
    """main(): one bad file in a batch must not abort processing of the rest."""

    def test_one_bad_file_does_not_abort_the_batch(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A batch with one broken file still reports the good file, and exits with code 3."""
        (tmp_path / "good.py").write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        (tmp_path / "broken.py").write_text("def broken(:\n", encoding="utf-8")

        exit_code = migration.main([str(tmp_path), "--min-python", "3.12"])

        assert_that(exit_code, equal_to(3))
        output = capsys.readouterr().out
        assert_that(output, contains_string("good.py"))
        assert_that(output, contains_string("broken.py"))

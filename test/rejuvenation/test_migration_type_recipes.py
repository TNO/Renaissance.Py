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
        report = migration.FileReport(path=Path("x.py"), result=result, error=None, diff=None)

        assert_that(migration.has_fixed(report), is_(expected_fixed))
        assert_that(migration.has_unsafe(report), is_(expected_unsafe))
        assert_that(migration.is_clean(report), is_(expected_clean))

    def test_error_report_is_neither_fixed_unsafe_nor_clean(self) -> None:
        """A report with no result (an error occurred) is False for every predicate."""
        report = migration.FileReport(path=Path("x.py"), result=None, error="boom", diff=None)

        assert_that(migration.has_fixed(report), is_(False))
        assert_that(migration.has_unsafe(report), is_(False))
        assert_that(migration.is_clean(report), is_(False))


class TestProcessFile:
    """process_file: the dry-run/apply mechanics and per-file error isolation."""

    def test_dry_run_leaves_file_byte_identical(self, tmp_path: Path) -> None:
        """Dry run (apply=False) never touches the file on disk, even when it would fix a name."""
        target = tmp_path / "mod.py"
        target.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")
        original_bytes = target.read_bytes()

        report = migration.process_file(target, apply=False, min_python=(3, 12))

        assert_that(target.read_bytes(), equal_to(original_bytes))
        assert_that(migration.has_fixed(report), is_(True))
        assert_that(report.diff, is_not(None))

    def test_apply_writes_migrated_content(self, tmp_path: Path) -> None:
        """apply=True actually writes the PEP 695-converted content to disk."""
        target = tmp_path / "mod.py"
        target.write_text(LEGACY_TYPEVAR_SOURCE, encoding="utf-8")

        report = migration.process_file(target, apply=True, min_python=(3, 12))

        assert_that(migration.has_fixed(report), is_(True))
        assert_that(target.read_text(encoding="utf-8"), contains_string("def identity[T]"))

    def test_unsafe_typevar_reported_but_not_written(self, tmp_path: Path) -> None:
        """A TypeVar exported via __all__ is reported unsafe and the file is left untouched."""
        target = tmp_path / "mod.py"
        target.write_text(UNSAFE_TYPEVAR_SOURCE, encoding="utf-8")
        original = target.read_text(encoding="utf-8")

        report = migration.process_file(target, apply=True, min_python=(3, 12))

        assert_that(migration.has_unsafe(report), is_(True))
        assert_that(target.read_text(encoding="utf-8"), equal_to(original))

    def test_syntax_error_reported_as_error_not_raised(self, tmp_path: Path) -> None:
        """A file that fails to parse is reported on FileReport.error, not raised."""
        target = tmp_path / "broken.py"
        target.write_text("def broken(:\n", encoding="utf-8")

        report = migration.process_file(target, apply=False, min_python=(3, 12))

        assert_that(report.error, is_not(None))
        assert_that(report.result, is_(None))

    def test_apply_composes_typevarcheck_and_typevartuplecheck(self, tmp_path: Path) -> None:
        """TypeVarCheck's [*Ts] bracket and TypeVarTupleCheck's Unpack[Ts]->*Ts compose in one pass."""
        target = tmp_path / "mod.py"
        target.write_text(TYPEVARTUPLE_SOURCE, encoding="utf-8")

        report = migration.process_file(target, apply=True, min_python=(3, 12))

        assert_that(migration.has_fixed(report), is_(True))
        output = target.read_text(encoding="utf-8")
        assert_that(output, contains_string("def foo[*Ts](*args: *Ts) -> None:"))
        assert_that(output, is_not(contains_string("Unpack")))

    def test_dry_run_diff_previews_both_recipes_changes(self, tmp_path: Path) -> None:
        """Dry-run's diff for a combined file previews both the [*Ts] bracket and the Unpack rewrite."""
        target = tmp_path / "mod.py"
        target.write_text(TYPEVARTUPLE_SOURCE, encoding="utf-8")

        report = migration.process_file(target, apply=False, min_python=(3, 12))

        assert_that(migration.has_fixed(report), is_(True))
        assert_that(report.diff, contains_string("def foo[*Ts]"))
        assert_that(report.diff, contains_string("*args: *Ts"))


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

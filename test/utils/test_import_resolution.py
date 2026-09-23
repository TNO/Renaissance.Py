"""Tests for renaissance.utils.import_resolution."""

from pathlib import Path

import pytest
from hamcrest import assert_that, has_entry, is_

from renaissance.utils.import_resolution import collect_project_imported_names, resolve_project_module


@pytest.fixture
def project_tree(tmp_path: Path) -> Path:
    """Build a small redis-py-shaped tree: redis/typing.py, redis/commands/{__init__,sibling,core}.py."""
    (tmp_path / "redis" / "commands").mkdir(parents=True)
    (tmp_path / "redis" / "typing.py").write_text("AnyKeyT = 1\n")
    (tmp_path / "redis" / "commands" / "__init__.py").write_text("Y = 1\n")
    (tmp_path / "redis" / "commands" / "sibling.py").write_text("Z = 1\n")
    (tmp_path / "redis" / "commands" / "core.py").write_text("from ..typing import AnyKeyT\n")
    return tmp_path


class TestResolveProjectModule:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("importing_file_rel", "module", "level", "expected_rel"),
        [
            ("redis/commands/core.py", "redis.typing", 0, "redis/typing.py"),
            ("redis/commands/core.py", "redis.commands", 0, "redis/commands/__init__.py"),
            ("redis/commands/core.py", "sibling", 1, "redis/commands/sibling.py"),
            ("redis/commands/core.py", "typing", 2, "redis/typing.py"),
            ("redis/commands/core.py", None, 1, "redis/commands/__init__.py"),
            ("redis/commands/core.py", "typing", 0, None),
            ("redis/commands/core.py", "nonexistent.module", 0, None),
        ],
    )
    def test_resolve(
        self,
        project_tree: Path,
        importing_file_rel: str,
        module: str | None,
        level: int,
        expected_rel: str | None,
    ) -> None:
        """Absolute, relative and package imports resolve to their project file, or None outside the project."""
        importing_file =project_tree / importing_file_rel
        expected = project_tree / expected_rel if expected_rel is not None else None
        assert_that(resolve_project_module(importing_file, project_tree, module, level), is_(expected))

    @pytest.mark.parametrize(
        ("module", "level"),
        [
            pytest.param("sibling", 2, id="parent-module"),
            pytest.param(None, 2, id="parent-package"),
        ],
    )
    def test_relative_import_above_relative_root_is_none(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        module: str | None,
        level: int,
    ) -> None:
        """A relative import walking above a relative project root (".") resolves to None."""
        (tmp_path / "sibling.py").write_text("X = 1\n")
        (tmp_path / "__init__.py").write_text("")
        monkeypatch.chdir(tmp_path)

        assert_that(resolve_project_module(Path("top.py"), Path(), module, level), is_(None))


class TestCollectProjectImportedNames:
    """See module docstring."""

    def test_maps_absolute_import_to_origin_file(self, project_tree: Path) -> None:
        """A name imported by one file is recorded against the file it is imported from."""
        files = [project_tree / "redis" / "typing.py", project_tree / "redis" / "commands" / "core.py"]
        result = collect_project_imported_names(files, project_tree)
        assert_that(result, has_entry(project_tree / "redis" / "typing.py", frozenset({"AnyKeyT"})))

    def test_records_original_name_not_alias(self, tmp_path: Path) -> None:
        """An aliased import is recorded under the name declared in the origin module."""
        (tmp_path / "origin.py").write_text("X = 1\n")
        (tmp_path / "consumer.py").write_text("from origin import X as Z\n")
        files = [tmp_path / "origin.py", tmp_path / "consumer.py"]
        result = collect_project_imported_names(files, tmp_path)
        assert_that(result, has_entry(tmp_path / "origin.py", frozenset({"X"})))

    def test_does_not_record_stdlib_import(self, tmp_path: Path) -> None:
        """An import that doesn't resolve inside the project is not recorded."""
        (tmp_path / "consumer.py").write_text("from typing import TypeVar\n")
        files = [tmp_path / "consumer.py"]
        result = collect_project_imported_names(files, tmp_path)
        assert_that(result, is_({}))

    def test_unrelated_same_name_in_two_files_does_not_collide(self, tmp_path: Path) -> None:
        """Two unrelated files declaring the same name, with no imports between them, record nothing."""
        (tmp_path / "a.py").write_text("T = 1\n")
        (tmp_path / "b.py").write_text("T = 2\n")
        files = [tmp_path / "a.py", tmp_path / "b.py"]
        result = collect_project_imported_names(files, tmp_path)
        assert_that(result, is_({}))

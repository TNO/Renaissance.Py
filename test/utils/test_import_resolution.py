"""Tests for renaissance.utils.import_resolution."""

from pathlib import Path

import pytest
from hamcrest import assert_that, has_entry, has_item, has_key, is_, is_not

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
        importing_file = project_tree / importing_file_rel
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


@pytest.fixture
def module_tree(tmp_path: Path) -> Path:
    """Build pkg/__init__.py and pkg/mod.py (declaring T) under tmp_path."""
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("X = 1\n")
    (tmp_path / "pkg" / "mod.py").write_text("T = 1\n")
    return tmp_path


class TestCollectModuleAttributeAccess:
    """collect_project_imported_names: names reached as attributes of an imported project module."""

    @pytest.mark.parametrize(
        ("consumer_source", "origin_rel", "expected"),
        [
            pytest.param("import pkg.mod\nx = pkg.mod.T\n", "pkg/mod.py", "T", id="import-dotted"),
            pytest.param("import pkg.mod as m\nx = m.T\n", "pkg/mod.py", "T", id="import-as"),
            pytest.param("from pkg import mod\nx = mod.T\n", "pkg/mod.py", "T", id="from-package-import-module"),
            pytest.param("from . import mod\nx = mod.T\n", "pkg/mod.py", "T", id="from-dot-import-module"),
            pytest.param("from pkg import mod as m\nx = m.T\n", "pkg/mod.py", "T", id="from-import-module-as"),
            pytest.param("import pkg.mod\nx = pkg.X\n", "pkg/__init__.py", "X", id="import-dotted-parent-package"),
        ],
    )
    def test_records_attribute_accessed_through_module_import(
        self,
        module_tree: Path,
        consumer_source: str,
        origin_rel: str,
        expected: str,
    ) -> None:
        """An attribute read through an imported project module is recorded against that module's file."""
        consumer = module_tree / "pkg" / "consumer.py"
        consumer.write_text(consumer_source)

        result = collect_project_imported_names([consumer], module_tree)

        assert_that(result, has_entry(module_tree / origin_rel, has_item(expected)))

    @pytest.mark.parametrize(
        "consumer_source",
        [
            pytest.param("import pkg.mod\n", id="module-imported-but-unused"),
            pytest.param("import pkg.mod\nx = other.T\n", id="attribute-on-unimported-name"),
            pytest.param("import typing\nx = typing.TypeVar\n", id="stdlib-module"),
            pytest.param("mod = object()\nx = mod.T\n", id="local-name-shadowing-module-name"),
        ],
    )
    def test_does_not_record_unrelated_attribute_access(self, module_tree: Path, consumer_source: str) -> None:
        """Attribute reads not made through an imported project module record nothing against it."""
        consumer = module_tree / "pkg" / "consumer.py"
        consumer.write_text(consumer_source)

        result = collect_project_imported_names([consumer], module_tree)

        assert_that(result, is_not(has_key(module_tree / "pkg" / "mod.py")))

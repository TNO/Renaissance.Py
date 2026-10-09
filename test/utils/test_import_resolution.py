"""Tests for renaissance.utils.import_resolution."""

import ast
from pathlib import Path
from typing import cast

import pytest
from hamcrest import assert_that, equal_to, has_item, has_key, not_

from renaissance.utils.import_resolution import collect_project_imported_names, rebase_relative_module, resolve_project_module


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
        assert_that(resolve_project_module(importing_file, project_tree, module, level), equal_to(expected))

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

        assert_that(resolve_project_module(Path("top.py"), Path(), module, level), equal_to(None))


class TestRebaseRelativeModule:
    """Tests for rebase_relative_module."""

    @pytest.mark.parametrize(
        ("via", "origin_file", "origin_import", "expected"),
        [
            pytest.param("from .file_1 import T", "file_1.py", "from ._compat import X", "._compat", id="same-dir"),
            pytest.param("from .sub.file_1 import T", "sub/file_1.py", "from ._compat import X", ".sub._compat", id="origin-in-subpackage"),
            pytest.param("from .sub.file_1 import T", "sub/file_1.py", "from .._compat import X", "._compat", id="origin-climbs-back"),
            pytest.param("from .file_1 import T", "file_1.py", "from .._compat import X", ".._compat", id="origin-climbs-above-via"),
            pytest.param("from .sub import T", "sub/__init__.py", "from ._compat import X", ".sub._compat", id="origin-is-package"),
            pytest.param("from . import T", "__init__.py", "from ._compat import X", "._compat", id="origin-is-current-package"),
            pytest.param("from pkg.file_1 import T", "pkg/file_1.py", "from ._compat import X", "pkg._compat", id="absolute-via"),
            pytest.param("from .file_1 import T", "file_1.py", "from typing import X", "typing", id="absolute-import"),
            pytest.param("from .file_1 import T", "file_1.py", "from . import X", ".", id="origin-imports-its-own-package"),
            pytest.param("from file_1 import T", "file_1.py", "from ._compat import X", None, id="origin-at-top-level"),
        ],
    )
    def test_rebase(self, via: str, origin_file: str, origin_import: str, expected: str | None) -> None:
        """The origin's `from <module> import` is rewritten to name the same module from the importing file, or None."""
        via_stmt = cast("ast.ImportFrom", ast.parse(via).body[0])
        origin_stmt = cast("ast.ImportFrom", ast.parse(origin_import).body[0])

        rebased = rebase_relative_module(via_stmt.module, via_stmt.level, Path(origin_file), origin_stmt.module, origin_stmt.level)

        assert_that(rebased, equal_to(expected))


class TestCollectProjectImportedNames:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("consumer_source", "expected"),
        [
            pytest.param("from origin import X\n", {"origin.py": frozenset({"X"})}, id="absolute-import"),
            pytest.param("from .origin import X\n", {"origin.py": frozenset({"X"})}, id="relative-import"),
            pytest.param("from origin import X as Z\n", {"origin.py": frozenset({"X"})}, id="aliased-import-records-original-name"),
            pytest.param("from typing import TypeVar\n", {}, id="stdlib-import-not-recorded"),
        ],
    )
    def test_records_imported_names_against_their_origin_file(
        self,
        tmp_path: Path,
        consumer_source: str,
        expected: dict[str, frozenset[str]],
    ) -> None:
        """A name imported from a project file is recorded against that file, under its declared name."""
        (tmp_path / "origin.py").write_text("X = 1\n")
        (tmp_path / "consumer.py").write_text(consumer_source)

        result = collect_project_imported_names([tmp_path / "origin.py", tmp_path / "consumer.py"], tmp_path)

        assert_that(result, equal_to({tmp_path / name: names for name, names in expected.items()}))


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

        assert_that(sorted(result.get(module_tree / origin_rel, frozenset[str]())), has_item(expected))

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

        assert_that(result, not_(has_key(module_tree / "pkg" / "mod.py")))

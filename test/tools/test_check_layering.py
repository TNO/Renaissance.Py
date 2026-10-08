"""Tests for the layer-boundary guard rail in tools/check_layering.py.

The `tools` directory is not on the pytest `pythonpath`, so the script is loaded from its path.
The unit tests run against synthetic package trees, so they stay valid when `src/` is restructured.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_check_layering() -> ModuleType:
    """Import tools/check_layering.py as a module."""
    path = ROOT / "tools" / "check_layering.py"
    spec = importlib.util.spec_from_file_location("check_layering", path)
    if spec is None or spec.loader is None:
        message = f"cannot load {path}"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_layering = _load_check_layering()


@pytest.fixture
def source_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return an empty source tree with two layers: `bindings` may import `core`, but not the other way around."""
    monkeypatch.setattr(check_layering, "LAYERS", {"core": ("core",), "bindings": ("bindings",)})
    monkeypatch.setattr(check_layering, "ALLOWED_DEPENDENCIES", {"core": frozenset[str](), "bindings": frozenset({"core"})})
    monkeypatch.setattr(check_layering, "ALLOWLIST", ())
    for package in ("core", "bindings"):
        (tmp_path / package).mkdir()
        (tmp_path / package / "__init__.py").write_text("", encoding="utf-8")
    return tmp_path


def _write(source_root: Path, relative: str, source: str) -> None:
    """Write `source` to `relative` inside `source_root`, creating the packages on the way."""
    path = source_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    for package in path.parents:
        if package == source_root:
            break
        (package / "__init__.py").touch()
    path.write_text(source, encoding="utf-8")


def _pairs(source_root: Path) -> list[tuple[str, str]]:
    """Return the (module, imported module) pair of every violation found below `source_root`."""
    return [(violation.module, violation.imported) for violation in check_layering.find_violations(source_root)]


def test_import_of_a_lower_layer_is_allowed(source_root: Path) -> None:
    """Assert a parser binding may import the core."""
    _write(source_root, "bindings/parser.py", "from core.node import Node\n")
    assert _pairs(source_root) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_import_of_a_higher_layer_is_reported(source_root: Path) -> None:
    """Assert the core may not import a parser binding."""
    _write(source_root, "core/node.py", "from bindings.parser import Parser\n")
    assert _pairs(source_root) == [("core.node", "bindings.parser")]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_relative_import_is_resolved_before_it_is_judged(source_root: Path) -> None:
    """Assert a relative import that leaves the layer is resolved to its absolute module and reported."""
    _write(source_root, "core/deep/node.py", "from ...bindings.parser import Parser\n")
    assert _pairs(source_root) == [("core.deep.node", "bindings.parser")]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_import_inside_a_function_is_reported(source_root: Path) -> None:
    """Assert a deferred import does not escape the check."""
    _write(source_root, "core/node.py", "def build():\n    from bindings.parser import Parser\n    return Parser\n")
    assert _pairs(source_root) == [("core.node", "bindings.parser")]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_type_checking_import_is_reported_and_flagged(source_root: Path) -> None:
    """Assert an import that only exists for the type checker is reported, and marked as such."""
    _write(source_root, "core/node.py", "from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    from bindings.parser import Parser\n")
    violations = check_layering.find_violations(source_root)
    flags = [(violation.imported, violation.type_checking_only) for violation in violations]
    assert flags == [("bindings.parser", True)]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_same_layer_and_external_imports_are_ignored(source_root: Path) -> None:
    """Assert imports within a layer, and imports of packages no layer owns, are not violations."""
    _write(source_root, "core/node.py", "import json\n\nfrom core.text import Text\nfrom clang.cindex import Cursor\n")
    assert _pairs(source_root) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_allowlisted_violation_does_not_fail_the_check(source_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Assert a violation listed with its reason is reported but accepted."""
    _write(source_root, "core/node.py", "from bindings.parser import Parser\n")
    exemption = check_layering.Exemption(module="core.node", imported="bindings.parser", reason="accepted for this test")
    monkeypatch.setattr(check_layering, "ALLOWLIST", (exemption,))
    monkeypatch.setattr(check_layering, "SOURCE_ROOT", source_root)
    monkeypatch.setattr(check_layering, "ROOT", source_root)
    assert check_layering.main([]) == check_layering.EXIT_OK  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_stale_allowlist_entry_fails_the_check(source_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Assert an allowlist entry that no longer matches a violation fails, so the allowlist cannot rot."""
    exemption = check_layering.Exemption(module="core.node", imported="bindings.parser", reason="already resolved")
    monkeypatch.setattr(check_layering, "ALLOWLIST", (exemption,))
    monkeypatch.setattr(check_layering, "SOURCE_ROOT", source_root)
    monkeypatch.setattr(check_layering, "ROOT", source_root)
    assert check_layering.main([]) == check_layering.EXIT_VIOLATIONS  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_violation_outside_the_allowlist_fails_the_check(source_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Assert an unknown violation fails the check."""
    _write(source_root, "core/node.py", "from bindings.parser import Parser\n")
    monkeypatch.setattr(check_layering, "SOURCE_ROOT", source_root)
    monkeypatch.setattr(check_layering, "ROOT", source_root)
    assert check_layering.main(["--check"]) == check_layering.EXIT_VIOLATIONS  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_the_known_violations_of_the_source_tree_are_found() -> None:
    """Assert the core-to-binding imports that the allowlist describes are the ones the tool reports."""
    found = {(violation.module, violation.imported) for violation in check_layering.find_violations(ROOT / "src")}
    known = {(exemption.module, exemption.imported) for exemption in check_layering.ALLOWLIST}
    assert known <= found  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)

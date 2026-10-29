# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the layout guard rail in tools/check_layout.py.

The unit tests check synthetic file lists; one integration test runs git in a temporary repository.
"""

import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path

import pytest

from tools import check_layout

TESTS_OF_TOOLS = {"code": "tools", "units": "modules", "mirror": "test/tools/test_{path}.py"}
PAGES_OF_TOOLS = {"code": "tools", "units": "modules", "mirror": "docs/tools/{kebab_path}.md"}
TESTS_OF_CORE = {"code": "src/core", "units": "packages", "mirror": "test/unit/core/{path}/"}


def _violations(entry: Mapping[str, object], files: set[str]) -> list[str]:
    """Return the violations of the mirror `entry` for the repository holding `files`, as reported."""
    (mirror,) = check_layout.parse_mirrors({"mirrors": [entry]})
    return [violation.describe() for violation in check_layout.check_mirror(mirror, files)]


def test_a_module_with_its_counterpart_passes() -> None:
    """Assert a module with its test file passes, and that `__init__.py` and helpers in the mirror are ignored."""
    files = {"tools/__init__.py", "tools/check_a.py", "test/tools/test_check_a.py", "test/tools/conftest.py"}
    assert _violations(TESTS_OF_TOOLS, files) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_module_without_its_counterpart_is_reported() -> None:
    """Assert a module without its test file is reported with the path the test file needs."""
    violations = _violations(TESTS_OF_TOOLS, {"tools/check_a.py"})
    assert violations == ["tools/check_a.py: has no counterpart test/tools/test_check_a.py"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_counterpart_without_its_unit_is_reported() -> None:
    """Assert a test file left behind by a renamed module is reported."""
    files = {"tools/check_b.py", "test/tools/test_check_a.py", "test/tools/test_check_b.py"}
    violations = _violations(TESTS_OF_TOOLS, files)
    assert violations == ["test/tools/test_check_a.py: mirrors no unit of tools/"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_the_modules_of_a_sub_package_are_no_units() -> None:
    """Assert only the modules directly in `code` are units; a sub-package needs a mirror of its own."""
    files = {"tools/check_a.py", "tools/shared/__init__.py", "tools/shared/runner.py", "test/tools/test_check_a.py"}
    assert _violations(TESTS_OF_TOOLS, files) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_the_kebab_path_placeholder_replaces_underscores() -> None:
    """Assert `{kebab_path}` spells `check_a_b` as `check-a-b`."""
    assert _violations(PAGES_OF_TOOLS, {"tools/check_a_b.py", "docs/tools/check-a-b.md"}) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_packages_are_mirrored_by_directories_at_every_depth() -> None:
    """Assert every package below `code`, but not `code` itself, needs a directory holding a file."""
    files = {
        "src/core/__init__.py",
        "src/core/model/__init__.py",
        "src/core/model/node.py",
        "src/core/model/sub/__init__.py",
        "test/unit/core/model/test_node.py",
    }
    violations = _violations(TESTS_OF_CORE, files)
    assert violations == ["src/core/model/sub/: has no counterpart test/unit/core/model/sub/"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_directory_without_its_package_is_reported() -> None:
    """Assert a test directory that mirrors no package is reported, and that an extra is accepted."""
    files = {
        "src/core/model/__init__.py",
        "test/unit/core/model/test_node.py",
        "test/unit/core/matching/test_finder.py",
        "test/unit/core/model/data/input.py",
    }
    entry = {**TESTS_OF_CORE, "extra": ["test/unit/core/model/data/"]}
    violations = _violations(entry, files)
    assert violations == ["test/unit/core/matching/: mirrors no unit of src/core/"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_an_exempt_unit_needs_no_counterpart() -> None:
    """Assert an exempt unit without counterpart passes."""
    entry = {**TESTS_OF_TOOLS, "exempt": ["check_a"]}
    assert _violations(entry, {"tools/check_a.py"}) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_stale_deviations_are_reported() -> None:
    """Assert exemptions and extras that no longer describe a deviation fail, so the lists only shrink."""
    entry = {
        **TESTS_OF_TOOLS,
        "exempt": ["check_a", "check_gone"],
        "extra": ["test/tools/test_check_a.py", "test/tools/missing.py"],
    }
    violations = _violations(entry, {"tools/check_a.py", "test/tools/test_check_a.py"})
    assert violations == [  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
        "tools/check_a.py: is exempt, but test/tools/test_check_a.py exists: remove the exemption",
        "tools/check_gone: is exempt, but is not a unit: remove the exemption",
        "test/tools/missing.py: is an extra of the mirror of tools/, but does not exist: remove it",
        "test/tools/test_check_a.py: is an extra of the mirror of tools/, but is a counterpart: remove it",
    ]


@pytest.mark.parametrize(
    ("config", "message"),
    [
        ({}, "at least one"),
        ({"mirrors": [{**TESTS_OF_TOOLS, "unit": "modules"}]}, "unknown key"),
        ({"mirrors": [{**TESTS_OF_TOOLS, "code": "tools/"}]}, "`code`"),
        ({"mirrors": [{**TESTS_OF_TOOLS, "units": "files"}]}, "`units`"),
        ({"mirrors": [{**TESTS_OF_TOOLS, "mirror": "test/tools/test.py"}]}, "exactly one"),
        ({"mirrors": [{**TESTS_OF_TOOLS, "mirror": "{path}/{kebab_path}.md"}]}, "exactly one"),
        ({"mirrors": [{**TESTS_OF_TOOLS, "exempt": "check_a"}]}, "list of strings"),
        ({"mirrors": [{**TESTS_OF_TOOLS, "exempt": ["check_a", "check_a"]}]}, "twice"),
    ],
)
def test_an_invalid_configuration_is_rejected(config: Mapping[str, object], message: str) -> None:
    """Assert a configuration that does not describe valid mirrors raises `ConfigError`."""
    with pytest.raises(check_layout.ConfigError, match=message):
        check_layout.parse_mirrors(config)


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_untracked_files_count_and_ignored_files_do_not(tmp_path: Path) -> None:
    """Assert the files are those git tracks or would track: a new file counts, an ignored one does not."""
    git = shutil.which("git")
    assert git is not None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    subprocess.run([git, "init", "-q"], cwd=tmp_path, check=True)  # noqa: S603 (git from PATH, fixed arguments)
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "check_a.py").write_text("")
    (tmp_path / "tools" / "ignored.py").write_text("")
    assert check_layout.list_files(tmp_path) == {".gitignore", "tools/check_a.py"}  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_the_repository_mirrors_its_code() -> None:
    """Assert the repository itself passes its own `[tool.check_layout]`."""
    assert check_layout.main([]) == check_layout.EXIT_OK  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)

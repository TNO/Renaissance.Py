# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the source-root guard rail in tools/check_source_roots.py."""

from typing import Any

import pytest

from tools import check_source_roots


def _config(pythonpath: list[str], src: list[str], extra_paths: list[str]) -> dict[str, Any]:
    """Return a parsed pyproject.toml that holds the three source-root settings."""
    return {
        "tool": {
            "pytest": {"ini_options": {"pythonpath": pythonpath}},
            "ruff": {"src": src},
            "pyright": {"extraPaths": extra_paths},
        }
    }


def test_the_settings_are_read_by_their_description() -> None:
    """Assert each setting is read from its table and named as pyproject.toml writes it."""
    values = check_source_roots.read_source_roots(_config(["a"], ["b"], ["c"]))
    expected = {"[tool.pytest.ini_options] pythonpath": ["a"], "[tool.ruff] src": ["b"], "[tool.pyright] extraPaths": ["c"]}
    assert values == expected  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_equal_settings_agree() -> None:
    """Assert three settings with the same source roots pass."""
    roots = ["src", "test"]
    assert check_source_roots.agree(check_source_roots.read_source_roots(_config(roots, roots, roots)))  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.mark.parametrize(
    ("pythonpath", "src", "extra_paths"),
    [
        (["src", "test"], ["src", "test"], ["src"]),
        (["src", "test"], ["test", "src"], ["src", "test"]),
    ],
    ids=["a root is missing", "the order differs"],
)
def test_differing_settings_disagree(pythonpath: list[str], src: list[str], extra_paths: list[str]) -> None:
    """Assert a setting that lacks a root, or lists the roots in another order, is a violation."""
    assert not check_source_roots.agree(check_source_roots.read_source_roots(_config(pythonpath, src, extra_paths)))  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_missing_setting_is_rejected() -> None:
    """Assert a configuration without one of the settings cannot be checked."""
    config = _config(["src"], ["src"], ["src"])
    del config["tool"]["ruff"]
    with pytest.raises(ValueError, match=r"\[tool\.ruff\] src is missing"):
        check_source_roots.read_source_roots(config)


def test_the_repository_lists_the_same_source_roots() -> None:
    """Assert the pyproject.toml of this repository passes the check."""
    assert check_source_roots.main([]) == check_source_roots.EXIT_OK  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for running the linters in tools/shared/linters.py.

The tests run ruff, a development dependency, on small inputs; counting the pyright issues is left to the lint budget in CI.
"""

from pathlib import Path

import pytest

from tools.shared import linters


def test_a_json_array_is_parsed() -> None:
    """Assert the JSON array that ruff prints is returned as a list of objects."""
    groups = linters.run_json_array("ruff", ["linter", "--output-format", "json"])
    assert any(group.get("prefix") == "F" for group in groups)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_failing_tool_raises() -> None:
    """Assert an exit code above the accepted one raises, naming the tool."""
    with pytest.raises(RuntimeError, match=r"ruff.* failed"):
        linters.run_json_array("ruff", ["check", "--no-such-option"])


def test_output_without_json_raises() -> None:
    """Assert output without a JSON array raises instead of being parsed."""
    with pytest.raises(RuntimeError, match="no JSON output"):
        linters.run_json_array("ruff", ["version"])


def test_ruff_issues_are_counted_per_rule_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Assert every issue counts once for its rule code, with every rule selected."""
    modules = ["os", "sys"]
    source = tmp_path / "example.py"
    source.write_text("".join(f"import {module}\n" for module in modules), encoding="utf-8")
    monkeypatch.setattr(linters, "CHECK_PATHS", (str(source),))
    assert linters.count_ruff_issues()["F401"] == len(modules)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)

"""AI: Tests for the ruff/pyright issue budget gate in tools/lint_budget.py.

The `tools` directory is not on the pytest `pythonpath`, so the script is loaded from its path.
"""

import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_lint_budget():
    """AI: Import tools/lint_budget.py as a module."""
    spec = importlib.util.spec_from_file_location("lint_budget", ROOT / "tools" / "lint_budget.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint_budget = _load_lint_budget()


@pytest.fixture
def budget_file(tmp_path, monkeypatch):
    """AI: Redirect the budget file to a temporary location."""
    path = tmp_path / "lint-budget.json"
    monkeypatch.setattr(lint_budget, "BUDGET_FILE", path)
    return path


def _stub_counts(monkeypatch, ruff: dict[str, int], pyright: dict[str, int]) -> None:
    """AI: Replace the ruff and pyright runs by fixed issue counts."""
    monkeypatch.setattr(lint_budget, "COUNTERS", {"ruff": lambda: Counter(ruff), "pyright": lambda: Counter(pyright)})


def test_unchanged_counts_are_within_budget() -> None:
    """AI: Assert equal counts are neither exceeded nor improved."""
    assert lint_budget.compare("ruff", Counter({"E501": 3}), {"E501": 3}) == ([], [])


def test_more_issues_of_a_budgeted_kind_exceed_the_budget() -> None:
    """AI: Assert an extra issue of an existing kind is reported as exceeding its budget."""
    exceeded, improved = lint_budget.compare("ruff", Counter({"E501": 4}), {"E501": 3})
    assert len(exceeded) == 1
    assert "E501" in exceeded[0]
    assert improved == []


def test_a_new_kind_of_issue_exceeds_its_zero_budget() -> None:
    """AI: Assert a kind without a budget entry may not occur at all."""
    exceeded, improved = lint_budget.compare("ruff", Counter({"E501": 3, "D100": 1}), {"E501": 3})
    assert len(exceeded) == 1
    assert "D100" in exceeded[0]
    assert improved == []


def test_fewer_issues_are_reported_as_improvement() -> None:
    """AI: Assert a reduced count is reported as an improvement rather than a failure."""
    exceeded, improved = lint_budget.compare("ruff", Counter({"E501": 1}), {"E501": 3, "D100": 2})
    assert exceeded == []
    assert len(improved) == 2


def test_check_fails_when_a_new_issue_is_introduced(budget_file, monkeypatch) -> None:
    """AI: Assert the gate fails and keeps the budget when a pull request adds an issue."""
    budget_file.write_text(json.dumps({"ruff": {"E501": 1}, "pyright": {}}), encoding="utf-8")
    _stub_counts(monkeypatch, ruff={"E501": 2}, pyright={})

    assert lint_budget.main([]) == lint_budget.EXIT_OVER_BUDGET
    assert json.loads(budget_file.read_text(encoding="utf-8"))["ruff"] == {"E501": 1}


def test_reduced_counts_are_adopted_as_the_new_budget(budget_file, monkeypatch) -> None:
    """AI: Assert the budget ratchets down to the reduced counts."""
    budget_file.write_text(json.dumps({"ruff": {"E501": 5}, "pyright": {"reportUnusedVariable": 2}}), encoding="utf-8")
    _stub_counts(monkeypatch, ruff={"E501": 3}, pyright={"reportUnusedVariable": 2})

    assert lint_budget.main([]) == lint_budget.EXIT_OK
    assert json.loads(budget_file.read_text(encoding="utf-8")) == {"ruff": {"E501": 3}, "pyright": {"reportUnusedVariable": 2}}


def test_check_mode_accepts_an_improvement_without_writing(budget_file, monkeypatch, capsys) -> None:
    """AI: Assert CI mode passes a pull request that lowers the counts and never writes the budget file."""
    budget_file.write_text(json.dumps({"ruff": {"E501": 5}, "pyright": {}}), encoding="utf-8")
    _stub_counts(monkeypatch, ruff={"E501": 3}, pyright={})

    assert lint_budget.main(["--check"]) == lint_budget.EXIT_OK
    assert "improved" in capsys.readouterr().out
    assert json.loads(budget_file.read_text(encoding="utf-8"))["ruff"] == {"E501": 5}


def test_removal_is_advised_when_no_issues_are_left(budget_file, monkeypatch, capsys) -> None:
    """AI: Assert the user is told the budget functionality can be removed once all issues are gone."""
    budget_file.write_text(json.dumps({"ruff": {"E501": 1}, "pyright": {}}), encoding="utf-8")
    _stub_counts(monkeypatch, ruff={}, pyright={})

    assert lint_budget.main([]) == lint_budget.EXIT_OK
    assert "can be removed" in capsys.readouterr().out
    assert json.loads(budget_file.read_text(encoding="utf-8")) == {"ruff": {}, "pyright": {}}

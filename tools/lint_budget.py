# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Budget-based gate for ruff and pyright issues.

The repository cannot enable every ruff rule and pyright's strict mode yet: the existing
issues would fail CI. Instead of disabling those checks, this script runs the strict
configuration, counts the issues per kind (ruff rule code, pyright rule name), and compares
the counts with a per-kind budget stored in `lint-budget.json`:

* a pull request may never exceed the budget of any kind (new issues fail the check);
* a reduction never fails the check: improving the code is always allowed, and the lower
  counts are adopted as the new budget, so the counts can only ratchet down;
* once every count reaches zero the budget file, this script, `pyrightconfig.strict.json`
  and the CI step can be removed, and the strict settings can move into `pyproject.toml`.

Run `python -m tools.lint_budget` to check and adopt improvements, and
`python -m tools.lint_budget --check` (as CI does) to check without writing; the
`lint budget` workflow adopts the improvements on `main` in a pull request of its own.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from tools.shared.linters import PYRIGHT_STRICT_CONFIG, ROOT, count_pyright_issues, count_ruff_issues

BUDGET_FILE = ROOT / "lint-budget.json"

EXIT_OK = 0
EXIT_OVER_BUDGET = 1
EXIT_TOOL_FAILURE = 2

COUNTERS = {"ruff": count_ruff_issues, "pyright": count_pyright_issues}


def load_budget() -> dict[str, dict[str, int]]:
    """AI: Read the per-kind budgets, treating a missing file as an empty budget."""
    if not BUDGET_FILE.exists():
        return {}
    return json.loads(BUDGET_FILE.read_text(encoding="utf-8"))


def save_budget(budget: dict[str, dict[str, int]]) -> None:
    """AI: Write the per-kind budgets as sorted JSON, so updates produce minimal diffs."""
    BUDGET_FILE.write_text(json.dumps(budget, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare(tool: str, counts: Counter[str], budgets: dict[str, int]) -> tuple[list[str], list[str]]:
    """AI: Describe the kinds of `tool` that exceed their budget and the kinds that improved."""
    exceeded: list[str] = []
    improved: list[str] = []
    for kind in sorted(set(counts) | set(budgets)):
        current = counts.get(kind, 0)
        budget = budgets.get(kind, 0)
        if current > budget:
            exceeded.append(f"  {tool} {kind}: {current} issues, budget {budget} (+{current - budget})")
        elif current < budget:
            improved.append(f"  {tool} {kind}: {current} issues, budget was {budget} (-{budget - current})")
    return exceeded, improved


def _removal_advice() -> str:
    """AI: Explain that the budget machinery is no longer needed."""
    return (
        "\nNo ruff or pyright issues are left. This budget functionality can be removed:\n"
        '  1. move the strict settings into pyproject.toml (ruff `select = ["ALL"]`, pyright `typeCheckingMode = "strict"`);\n'
        f"  2. delete {BUDGET_FILE.name}, {PYRIGHT_STRICT_CONFIG.name} and tools/{Path(__file__).name};\n"
        "  3. delete the 'Check ruff and pyright issue budgets' step from .github/workflows/code-quality.yml."
    )


def main(argv: list[str] | None = None) -> int:
    """AI: Check the issue counts against their budgets and adopt every reduction."""
    parser = argparse.ArgumentParser(description="Check ruff and pyright issue counts against their per-kind budgets.")
    parser.add_argument("--check", action="store_true", help="only report; never update the budget file (used by CI)")
    parser.add_argument("--init", action="store_true", help="record the current counts as the budget (first run or an approved exception)")
    parser.add_argument("--tool", choices=("all", *COUNTERS), default="all", help="restrict the check to a single tool")
    args = parser.parse_args(argv)

    tools = tuple(COUNTERS) if args.tool == "all" else (args.tool,)
    try:
        counts = {tool: COUNTERS[tool]() for tool in tools}
    except (RuntimeError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return EXIT_TOOL_FAILURE

    budget = load_budget()
    if args.init:
        for tool in tools:
            budget[tool] = dict(sorted(counts[tool].items()))
        save_budget(budget)
        print(f"Recorded the current counts as the budget in {BUDGET_FILE.name}.")
        return EXIT_OK

    exceeded: list[str] = []
    improved: list[str] = []
    for tool in tools:
        tool_exceeded, tool_improved = compare(tool, counts[tool], budget.get(tool, {}))
        exceeded += tool_exceeded
        improved += tool_improved
        print(f"{tool}: {counts[tool].total()} issues in {len(counts[tool])} kinds, budget {sum(budget.get(tool, {}).values())}")

    if exceeded:
        print("\nThese kinds of issues exceed their budget:")
        print("\n".join(exceeded))
        print("\nFix them, or ask for an exception; the budget is never raised automatically.")
        print("CI checks your branch merged with main, so merge main into your branch when the issues are not yours.")
        return EXIT_OVER_BUDGET

    if improved:
        print("\nThese kinds of issues improved:")
        print("\n".join(improved))
        if args.check:
            # An improvement is not a failure: the budget is a ceiling, and the 'lint budget' workflow lowers it on main.
            print(f"\n{BUDGET_FILE.name} is out of date: run `python -m tools.lint_budget`, or let the 'lint budget' workflow lower it.")
        else:
            for tool in tools:
                budget[tool] = dict(sorted(counts[tool].items()))
            save_budget(budget)
            print(f"\nAdopted the lower counts as the new budget in {BUDGET_FILE.name}.")

    if args.tool == "all" and not any(counts[tool] for tool in tools):
        print(_removal_advice())
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

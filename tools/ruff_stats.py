"""AI: Report the ruff violation counts grouped by the prefix used in `select` and `ignore`.

`tools/lint_budget.py` counts the issues per rule code; this script aggregates the same counts per
linter prefix (`E`, `PLC`, `SIM`, ...), because that is the granularity at which `[tool.ruff.lint]`
in pyproject.toml switches a whole group of checks on or off. Prefixes without a single violation
can be added to `select` right away, so they are listed separately; `--format toml` prints the
extended selection ready to paste into pyproject.toml.

Run `python tools/ruff_stats.py` for the table, `--format json` for machine-readable output.
"""

import argparse
import json
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from typing import Any

from lint_budget import EXIT_OK, EXIT_TOOL_FAILURE, PYPROJECT_FILE, _parse_json, _run, _tool_command, count_ruff_issues

UNGROUPED = "-"


@dataclass(frozen=True)
class Group:
    """AI: A prefix that can be used as a `select`/`ignore` entry, with its linter and parent prefix."""

    prefix: str
    linter: str
    parent: str | None


@dataclass
class Statistics:
    """AI: What a single prefix contributes to the violations of the repository."""

    group: Group
    violations: int
    violated_rules: int
    total_rules: int
    selected: bool


def _ruff_json(*arguments: str) -> list[dict[str, Any]]:
    """AI: Run `ruff` with `arguments` and parse the JSON array it prints."""
    return _parse_json(_run([*_tool_command("ruff"), *arguments], max_exit_code=0), "[")


def linter_groups() -> list[Group]:
    """AI: List every prefix ruff accepts as a selector, expanding linters that have categories."""
    groups: list[Group] = []
    for linter in _ruff_json("linter", "--output-format", "json"):
        # A category prefix extends the prefix of its linter: pycodestyle "" + "E", Pylint "PL" + "C".
        categories = linter.get("categories")
        if categories:
            groups += [
                Group(linter["prefix"] + category["prefix"], f"{linter['name']} ({category['name']})", linter["prefix"] or None)
                for category in categories
            ]
        else:
            groups.append(Group(linter["prefix"], linter["name"], None))
    return groups


def _group_lookup(groups: list[Group]) -> dict[str, str]:
    """AI: Map every rule code to its prefix, preferring the longest match (`C4` over `C`, `PLC` over `PL`)."""
    prefixes = sorted((group.prefix for group in groups), key=len, reverse=True)
    # Ruff is moving to named rules; those have no code and therefore no prefix that pyproject.toml can select.
    codes = [rule["code"] for rule in _ruff_json("rule", "--all", "--output-format", "json") if rule.get("code")]
    return {code: next((prefix for prefix in prefixes if code.startswith(prefix)), UNGROUPED) for code in codes}


def selected_prefixes() -> set[str]:
    """AI: Read the prefixes that pyproject.toml currently selects."""
    with PYPROJECT_FILE.open("rb") as file:
        return set(tomllib.load(file)["tool"]["ruff"]["lint"]["select"])


def collect() -> list[Statistics]:
    """AI: Count the violations of every prefix with all rules selected and the configured ignores applied."""
    groups = linter_groups()
    lookup = _group_lookup(groups)
    counts = count_ruff_issues()
    selected = selected_prefixes()

    violations: Counter[str] = Counter()
    violated_rules: Counter[str] = Counter()
    total_rules: Counter[str] = Counter(lookup.values())
    for code, count in counts.items():
        prefix = lookup.get(code, UNGROUPED)
        violations[prefix] += count
        violated_rules[prefix] += 1

    groups.append(Group(UNGROUPED, "not attributable to a rule", None))
    return [
        Statistics(
            group=group,
            violations=violations[group.prefix],
            violated_rules=violated_rules[group.prefix],
            total_rules=total_rules[group.prefix],
            selected="ALL" in selected or group.prefix in selected or (group.parent is not None and group.parent in selected),
        )
        for group in groups
        if total_rules[group.prefix] or violations[group.prefix]
    ]


def _sort(statistics: list[Statistics], by: str) -> list[Statistics]:
    """AI: Order the rows by prefix, or by descending violation count with the prefix as tie-breaker."""
    if by == "prefix":
        return sorted(statistics, key=lambda row: row.group.prefix)
    return sorted(statistics, key=lambda row: (-row.violations, row.group.prefix))


def _print_table(statistics: list[Statistics]) -> None:
    """AI: Print the per-prefix counts and the prefixes that can be selected without any fix; only `main` may call this."""
    width = max(len(row.group.linter) for row in statistics)
    print(f"{'prefix':<6} {'linter':<{width}} {'violations':>10} {'rules':>9}  selected")  # noqa: T201 (this script reports to stdout)
    for row in statistics:
        rules = f"{row.violated_rules}/{row.total_rules}"
        selected = "yes" if row.selected else "no"
        line = f"{row.group.prefix:<6} {row.group.linter:<{width}} {row.violations:>10} {rules:>9}  {selected}"
        print(line)  # noqa: T201 (this script reports to stdout)

    total = sum(row.violations for row in statistics)
    violating = sum(1 for row in statistics if row.violations)
    unselected = [row for row in statistics if not row.selected]
    clean = sorted(row.group.prefix for row in unselected if not row.violations and row.group.prefix != UNGROUPED)
    summary = f"\n{total} violations in {violating} of the {len(statistics)} prefixes; {len(unselected)} are not selected yet."
    print(summary)  # noqa: T201 (this script reports to stdout)
    if clean:
        advice = f"\nThese {len(clean)} prefixes have no violations and can be added to `select` as they are:"
        print(advice)  # noqa: T201 (this script reports to stdout)
        print("  " + ", ".join(f'"{prefix}"' for prefix in clean))  # noqa: T201 (this script reports to stdout)


def _print_json(statistics: list[Statistics]) -> None:
    """AI: Print the rows as JSON, so other tooling can consume them; only `main` may call this."""
    rows = [
        {
            "prefix": row.group.prefix,
            "linter": row.group.linter,
            "violations": row.violations,
            "violated_rules": row.violated_rules,
            "total_rules": row.total_rules,
            "selected": row.selected,
        }
        for row in statistics
    ]
    print(json.dumps(rows, indent=2))  # noqa: T201 (this script reports to stdout)


def _print_toml(statistics: list[Statistics]) -> None:
    """AI: Print the `select` list that adds every prefix without violations to the current selection; only `main` may call this."""
    prefixes = sorted({row.group.prefix for row in statistics if (row.selected or not row.violations) and row.group.prefix != UNGROUPED})
    print("[tool.ruff.lint]")  # noqa: T201 (this script reports to stdout)
    print("select = [")  # noqa: T201 (this script reports to stdout)
    for start in range(0, len(prefixes), 10):
        line = ", ".join(f'"{prefix}"' for prefix in prefixes[start : start + 10])
        print(f"    {line},")  # noqa: T201 (this script reports to stdout)
    print("]")  # noqa: T201 (this script reports to stdout)


FORMATS = {"table": _print_table, "json": _print_json, "toml": _print_toml}


def main(argv: list[str] | None = None) -> int:
    """AI: Report the ruff violations per selectable prefix."""
    parser = argparse.ArgumentParser(description="Report ruff violation counts per linter prefix, the unit used in pyproject.toml.")
    parser.add_argument("--format", choices=FORMATS, default="table", help="how to report the statistics (default: table)")
    parser.add_argument("--sort", choices=("count", "prefix"), default="count", help="row order of the table (default: count)")
    parser.add_argument("--violations-only", action="store_true", help="omit the prefixes without a single violation")
    args = parser.parse_args(argv)

    try:
        statistics = collect()
    except (RuntimeError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)  # noqa: T201 (the tool failure is reported to stderr)
        return EXIT_TOOL_FAILURE

    if args.violations_only:
        statistics = [row for row in statistics if row.violations]
    FORMATS[args.format](_sort(statistics, args.sort))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

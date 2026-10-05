"""AI: Report the ruff violation counts grouped by the prefix used in `select` and `ignore`.

`tools/lint_budget.py` counts the issues per rule code; this script aggregates the same counts per
linter prefix (`E`, `PLC`, `SIM`, ...), because that is the granularity at which `[tool.ruff.lint]`
in pyproject.toml switches a whole group of checks on or off. Prefixes without a single violation
can be added to `select` right away, so they are listed separately; prefixes whose rules all live in
ruff's preview mode are listed apart, because selecting them has no effect without `preview = true`.
The `+preview` column shows how many violations each prefix gains when preview mode is enabled.
`--format toml` prints the extended selection ready to paste into pyproject.toml.

Run `python tools/ruff_stats.py` for the table, `--format json` for machine-readable output.
"""

import argparse
import json
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from typing import Any

from lint_budget import EXIT_OK, EXIT_TOOL_FAILURE, PYPROJECT_FILE, count_ruff_issues, run_json_array

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
    preview_only: bool
    preview_violations: int


def _ruff_json(*arguments: str) -> list[dict[str, Any]]:
    """AI: Run `ruff` with `arguments` and parse the JSON array it prints."""
    return run_json_array("ruff", list(arguments))


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


def _rule_facts(groups: list[Group]) -> tuple[dict[str, str], set[str]]:
    """AI: Map every rule code to its prefix (longest match: `C4` over `C`) and list the prefixes that only preview mode enables."""
    prefixes = sorted((group.prefix for group in groups), key=len, reverse=True)
    # Ruff is moving to named rules; those have no code and therefore no prefix that pyproject.toml can select.
    rules = [rule for rule in _ruff_json("rule", "--all", "--output-format", "json") if rule.get("code")]
    lookup = {rule["code"]: next((prefix for prefix in prefixes if rule["code"].startswith(prefix)), UNGROUPED) for rule in rules}
    stable = {lookup[rule["code"]] for rule in rules if not rule["preview"]}
    return lookup, set(lookup.values()) - stable


def selected_prefixes() -> set[str]:
    """AI: Read the prefixes that pyproject.toml currently selects."""
    with PYPROJECT_FILE.open("rb") as file:
        return set(tomllib.load(file)["tool"]["ruff"]["lint"]["select"])


def collect() -> list[Statistics]:
    """AI: Count the violations of every prefix with all rules selected and the configured ignores applied."""
    groups = linter_groups()
    lookup, preview_only = _rule_facts(groups)
    counts = count_ruff_issues()
    preview_counts = count_ruff_issues(preview=True)
    selected = selected_prefixes()

    violations: Counter[str] = Counter()
    violated_rules: Counter[str] = Counter()
    preview_violations: Counter[str] = Counter()
    total_rules: Counter[str] = Counter(lookup.values())
    for code, count in counts.items():
        prefix = lookup.get(code, UNGROUPED)
        violations[prefix] += count
        violated_rules[prefix] += 1
    for code, count in preview_counts.items():
        preview_violations[lookup.get(code, UNGROUPED)] += count

    groups.append(Group(UNGROUPED, "not attributable to a rule", None))
    return [
        Statistics(
            group=group,
            violations=violations[group.prefix],
            violated_rules=violated_rules[group.prefix],
            total_rules=total_rules[group.prefix],
            selected="ALL" in selected or group.prefix in selected or (group.parent is not None and group.parent in selected),
            preview_only=group.prefix in preview_only,
            preview_violations=preview_violations[group.prefix],
        )
        for group in groups
        if total_rules[group.prefix] or violations[group.prefix] or preview_violations[group.prefix]
    ]


def _sort(statistics: list[Statistics], by: str) -> list[Statistics]:
    """AI: Order the rows by prefix, or by descending violation count with the prefix as tie-breaker."""
    if by == "prefix":
        return sorted(statistics, key=lambda row: row.group.prefix)
    return sorted(statistics, key=lambda row: (-row.violations, row.group.prefix))


def _prefixes(prefixes: list[str]) -> str:
    """AI: Count `prefixes` in words, so the advice lines read well for a single prefix too."""
    return f"{len(prefixes)} prefix" if len(prefixes) == 1 else f"{len(prefixes)} prefixes"


def _print_table(statistics: list[Statistics]) -> None:
    """AI: Print the per-prefix counts and the prefixes that can be selected without any fix; only `main` may call this."""
    labels = {row.group.prefix: row.group.linter + (" (preview)" if row.preview_only else "") for row in statistics}
    width = max(len(label) for label in labels.values())
    header = f"{'prefix':<6} {'linter':<{width}} {'violations':>10} {'+preview':>9} {'rules':>9}  selected"
    print(header)  # noqa: T201 (this script reports to stdout)
    for row in statistics:
        rules = f"{row.violated_rules}/{row.total_rules}"
        extra = f"{row.preview_violations - row.violations:+}" if row.preview_violations != row.violations else ""
        selected = "yes" if row.selected else "no"
        line = f"{row.group.prefix:<6} {labels[row.group.prefix]:<{width}} {row.violations:>10} {extra:>9} {rules:>9}  {selected}"
        print(line)  # noqa: T201 (this script reports to stdout)

    total = sum(row.violations for row in statistics)
    violating = sum(1 for row in statistics if row.violations)
    coming = sum(row.preview_violations for row in statistics) - total
    unselected = [row for row in statistics if not row.selected]
    candidates = [row for row in unselected if not row.violations and row.group.prefix != UNGROUPED]
    clean = sorted(row.group.prefix for row in candidates if not row.preview_only)
    preview = sorted((row.group.prefix, row.preview_violations) for row in unselected if row.preview_only)
    summary = f"\n{total} violations in {violating} of the {len(statistics)} prefixes; {len(unselected)} are not selected yet."
    print(summary)  # noqa: T201 (this script reports to stdout)
    print(f"`preview = true` would add {coming} violations on top of that.")  # noqa: T201 (this script reports to stdout)
    if clean:
        advice = f"\n{_prefixes(clean)} without violations, ready to be added to `select`:"
        print(advice)  # noqa: T201 (this script reports to stdout)
        print("  " + ", ".join(f'"{prefix}"' for prefix in clean))  # noqa: T201 (this script reports to stdout)
    if preview:
        warning = f"\n{_prefixes([prefix for prefix, _ in preview])} only effective once `preview = true` is enabled:"
        print(warning)  # noqa: T201 (this script reports to stdout)
        print("  " + ", ".join(f'"{prefix}" ({count} violations)' for prefix, count in preview))  # noqa: T201 (this script reports to stdout)


def _print_json(statistics: list[Statistics]) -> None:
    """AI: Print the rows as JSON, so other tooling can consume them; only `main` may call this."""
    rows = [
        {
            "prefix": row.group.prefix,
            "linter": row.group.linter,
            "violations": row.violations,
            "preview_violations": row.preview_violations,
            "violated_rules": row.violated_rules,
            "total_rules": row.total_rules,
            "selected": row.selected,
            "preview_only": row.preview_only,
        }
        for row in statistics
    ]
    print(json.dumps(rows, indent=2))  # noqa: T201 (this script reports to stdout)


def _print_toml(statistics: list[Statistics]) -> None:
    """AI: Print the `select` list that adds every prefix without violations to the current selection; only `main` may call this."""
    # A preview-only prefix is left out: selecting it has no effect until `preview = true` is enabled.
    keep = [row for row in statistics if row.selected or (not row.violations and not row.preview_only)]
    prefixes = sorted({row.group.prefix for row in keep if row.group.prefix != UNGROUPED})
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

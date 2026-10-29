# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Guard rail that requires pytest, Ruff and Pyright to list the same source roots in `pyproject.toml`.

Each of the three tools needs the directories that hold the top-level packages. TOML cannot declare that list once and refer
to it, so `pyproject.toml` repeats it in three settings, and this check fails when one of them changes without the others.

Run `python -m tools.check_source_roots` locally, or `python -m tools.check_source_roots --check` as CI does; both report and
neither writes.
"""

import argparse
import sys
import tomllib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Each setting is the path of its table in pyproject.toml followed by its key.
SOURCE_ROOT_SETTINGS: tuple[tuple[str, ...], ...] = (
    ("tool", "pytest", "ini_options", "pythonpath"),
    ("tool", "ruff", "src"),
    ("tool", "pyright", "extraPaths"),
)

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_TOOL_FAILURE = 2


def describe(setting: tuple[str, ...]) -> str:
    """Return how `pyproject.toml` writes `setting`, for example `[tool.ruff] src`."""
    *table, key = setting
    return f"[{'.'.join(table)}] {key}"


def read_source_roots(config: Mapping[str, Any]) -> dict[str, Any]:
    """Return the value of each source-root setting in `config` by its description, or raise ValueError when one is missing."""
    values: dict[str, Any] = {}
    for setting in SOURCE_ROOT_SETTINGS:
        value: Any = config
        try:
            for key in setting:
                value = value[key]
        except (KeyError, TypeError) as error:
            message = f"{describe(setting)} is missing"
            raise ValueError(message) from error
        values[describe(setting)] = value
    return values


def agree(values: Mapping[str, Any]) -> bool:
    """Return whether every setting in `values` holds the same source roots, in the same order."""
    first, *others = values.values()
    return all(other == first for other in others)


def main(argv: list[str] | None = None) -> int:
    """Report the source-root settings in pyproject.toml and fail when they differ."""
    parser = argparse.ArgumentParser(description="Check that pytest, Ruff and Pyright list the same source roots in pyproject.toml.")
    # --check mirrors tools/lint_budget.py; this check never writes, so it only documents the CI invocation.
    parser.add_argument("--check", action="store_true", help="only report, never write (used by CI; this check never writes)")
    parser.parse_args(argv)

    pyproject = ROOT / "pyproject.toml"
    try:
        with pyproject.open("rb") as file:
            values = read_source_roots(tomllib.load(file))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(f"Could not check {pyproject}: {error}", file=sys.stderr)  # noqa: T201 (a script reports on stdout and stderr)
        return EXIT_TOOL_FAILURE

    passed = agree(values)
    if passed:
        report = [f"Source root check passed: {len(values)} settings in pyproject.toml list {next(iter(values.values()))}."]
    else:
        report = ["These settings in pyproject.toml must list the same source roots, in the same order:"]
        report += [f"  {name} = {value}" for name, value in values.items()]
        report.append("\nMake them equal; see docs/developer/tools/check-source-roots.md.")
    print("\n".join(report))  # noqa: T201 (a script reports on stdout and stderr)

    return EXIT_OK if passed else EXIT_VIOLATIONS


if __name__ == "__main__":
    raise SystemExit(main())

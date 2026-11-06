# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Guard rail that requires the tests and the documentation to mirror the code.

`[tool.check_layout]` of `pyproject.toml` lists the mirrors, and is their single source of truth. A mirror maps every unit of
code under one directory, a module or a package, onto its counterpart: a test file, a test directory or a documentation page.
The check fails on a unit without its counterpart, and on a path in the mirror that is the counterpart of no unit, so a renamed
or deleted unit cannot leave its tests or its page behind.

A mirror with `aspects = true` also accepts a counterpart split into one file per aspect: `{path}` followed by `___<aspect>`,
such as `test_x___parsing.py` next to or instead of `test_x.py`. Whether names are well formed is not checked here, but by
`tools/check_names.py`.

A mirror may list known deviations: `exempt` names units that have no counterpart, `extra` names paths in the mirror that are no
counterpart. An entry that no longer describes a deviation fails the check, so these lists only shrink.

The files are those that git tracks or would track: `git ls-files --cached --others --exclude-standard`. A directory exists when
it holds such a file.

Run `python -m tools.check_layout` locally, or `python -m tools.check_layout --check` as CI does; both report and neither writes.
"""

import argparse
import re
import sys
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from tools.shared.repository_files import list_files, with_directories

ROOT = Path(__file__).resolve().parents[1]

# The placeholder of a mirror template, replaced by the path of a unit.
PLACEHOLDER = "{path}"
# Separates the unit from the aspect in the name of a counterpart split per aspect.
ASPECT_SEPARATOR = "___"
UNIT_KINDS = ("modules", "packages")
INIT = "__init__.py"

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_TOOL_FAILURE = 2


class ConfigError(ValueError):
    """`[tool.check_layout]` does not describe valid mirrors."""


@dataclass(frozen=True)
class Mirror:
    """The rule that every unit of code under `code` has a counterpart, whose path is `template` filled in for the unit.

    A unit is a module (a `.py` file directly in `code`, other than `__init__.py`) or a package (a directory below `code` holding
    `__init__.py`), named by its path relative to `code`, without `.py`, separated by `/`. A template that ends with `/` names a
    directory. The modules of a sub-package of `code` are units of a mirror of that sub-package. With `aspects`, the counterpart
    may be split into files with `___<aspect>` after the unit.
    """

    code: str
    units: str
    template: str
    exempt: frozenset[str] = frozenset()
    extra: frozenset[str] = frozenset()
    aspects: bool = False

    def counterpart(self, unit: str) -> str:
        """Return the path of the counterpart of `unit`, when it is not split per aspect."""
        return self.template.replace(PLACEHOLDER, unit)

    def unit_of(self, path: str) -> str | None:
        """Return the unit whose counterpart `path` is, whether or not that unit exists, or None when `path` has no such shape."""
        before, after = self.template.split(PLACEHOLDER)
        aspect = f"(?:{ASPECT_SEPARATOR}[^/]+)?" if self.aspects else ""
        match = re.fullmatch(f"{re.escape(before)}(.+?){aspect}{re.escape(after)}", path)
        return None if match is None else match.group(1)

    def location(self, unit: str) -> str:
        """Return the path of `unit` relative to the repository root."""
        return f"{self.code}/{unit}.py" if self.units == "modules" else f"{self.code}/{unit}/"


@dataclass(frozen=True)
class Violation:
    """A path that breaks a mirror, and why."""

    path: str
    reason: str

    def describe(self) -> str:
        """Return one line naming the path and what is wrong with it."""
        return f"{self.path}: {self.reason}"


def _strings(entry: Mapping[str, object], key: str) -> frozenset[str]:
    """Return the list of strings `entry[key]`, or raise when it is something else."""
    value = entry.get(key, [])
    items = cast("list[object]", value) if isinstance(value, list) else None
    if items is None or not all(isinstance(item, str) for item in items):
        message = f"`{key}` must be a list of strings"
        raise ConfigError(message)
    strings = cast("list[str]", items)
    if len(set(strings)) != len(strings):
        message = f"`{key}` lists an entry twice"
        raise ConfigError(message)
    return frozenset(strings)


def parse_mirrors(config: Mapping[str, object]) -> list[Mirror]:
    """Return the mirrors of the `[tool.check_layout]` table `config`, or raise `ConfigError` when it is invalid."""
    entries = config.get("mirrors")
    if not isinstance(entries, list) or not entries:
        message = "[tool.check_layout] must contain at least one [[tool.check_layout.mirrors]] table"
        raise ConfigError(message)
    mirrors: list[Mirror] = []
    for item in cast("list[object]", entries):
        if not isinstance(item, dict):
            message = "each mirror must be a [[tool.check_layout.mirrors]] table"
            raise ConfigError(message)
        entry = cast("dict[str, object]", item)
        unknown = set(entry) - {"code", "units", "mirror", "exempt", "extra", "aspects"}
        if unknown:
            message = f"unknown key(s) {sorted(unknown)} in a mirror"
            raise ConfigError(message)
        code, units, template = entry.get("code"), entry.get("units"), entry.get("mirror")
        if not isinstance(code, str) or not code or code.endswith("/"):
            message = "`code` must be a directory relative to the repository root, without a trailing `/`"
            raise ConfigError(message)
        if not isinstance(units, str) or units not in UNIT_KINDS:
            message = f"`units` of the mirror of {code} must be one of {list(UNIT_KINDS)}"
            raise ConfigError(message)
        if not isinstance(template, str) or template.count(PLACEHOLDER) != 1:
            message = f"`mirror` of the mirror of {code} must contain {PLACEHOLDER} exactly once"
            raise ConfigError(message)
        aspects = entry.get("aspects", False)
        if not isinstance(aspects, bool):
            message = f"`aspects` of the mirror of {code} must be true or false"
            raise ConfigError(message)
        mirrors.append(Mirror(code, units, template, _strings(entry, "exempt"), _strings(entry, "extra"), aspects))
    return mirrors


def load_config(pyproject: Path) -> Mapping[str, object]:
    """Return the `[tool.check_layout]` table of `pyproject`."""
    with pyproject.open("rb") as file:
        return tomllib.load(file).get("tool", {}).get("check_layout", {})


def find_units(mirror: Mirror, files: Iterable[str]) -> set[str]:
    """Return the units of code of `mirror` among `files`."""
    prefix = f"{mirror.code}/"
    relative = [file.removeprefix(prefix) for file in files if file.startswith(prefix)]
    if mirror.units == "modules":
        return {path.removesuffix(".py") for path in relative if path.endswith(".py") and "/" not in path and path != INIT}
    return {path.removesuffix(f"/{INIT}") for path in relative if path.endswith(f"/{INIT}")}


def check_mirror(mirror: Mirror, files: set[str]) -> list[Violation]:
    """Return how `files` break `mirror`: units without counterpart, paths that mirror no unit, and stale deviations."""
    paths = with_directories(files)
    units = find_units(mirror, files)
    mirrored = {path: unit for path in sorted(paths) if (unit := mirror.unit_of(path)) is not None}
    violations: list[Violation] = []
    for unit in sorted(units):
        counterparts = [path for path, mirrored_unit in mirrored.items() if mirrored_unit == unit]
        if not counterparts and unit not in mirror.exempt:
            violations.append(Violation(mirror.location(unit), f"has no counterpart {mirror.counterpart(unit)}"))
        elif counterparts and unit in mirror.exempt:
            violations.append(Violation(mirror.location(unit), f"is exempt, but {counterparts[0]} exists: remove the exemption"))
    violations += [
        Violation(f"{mirror.code}/{unit}", "is exempt, but is not a unit: remove the exemption") for unit in sorted(mirror.exempt - units)
    ]
    violations += [
        Violation(path, f"mirrors no unit of {mirror.code}/")
        for path, unit in mirrored.items()
        if unit not in units and path not in mirror.extra
    ]
    violations += [
        Violation(path, f"is an extra of the mirror of {mirror.code}/, but does not exist: remove it")
        for path in sorted(mirror.extra - paths)
    ]
    violations += [
        Violation(path, f"is an extra of the mirror of {mirror.code}/, but is a counterpart: remove it")
        for path in sorted(mirror.extra & paths)
        if mirrored.get(path) in units
    ]
    return violations


def main(argv: list[str] | None = None) -> int:
    """Report where the tests and the documentation do not mirror the code, and fail on any such place."""
    parser = argparse.ArgumentParser(description="Check that the tests and the documentation mirror the code.")
    # --check mirrors tools/lint_budget.py; this check never writes, so it only documents the CI invocation.
    parser.add_argument("--check", action="store_true", help="only report, never write (used by CI; this check never writes)")
    parser.parse_args(argv)

    try:
        mirrors = parse_mirrors(load_config(ROOT / "pyproject.toml"))
        files = list_files(ROOT)
    except (ConfigError, OSError, RuntimeError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        print(f"Could not check the layout of {ROOT}: {error}", file=sys.stderr)  # noqa: T201 (a script reports on stdout and stderr)
        return EXIT_TOOL_FAILURE
    violations = [violation for mirror in mirrors for violation in check_mirror(mirror, files)]

    if violations:
        report = ["The tests and the documentation do not mirror the code:"]
        report += [f"  {violation.describe()}" for violation in violations]
        report.append(
            "\nAdd or move the counterpart, or record the deviation in [tool.check_layout] of pyproject.toml;"
            " see docs/developer/tools/check_layout.md."
        )
    else:
        unit_count = sum(len(find_units(mirror, files)) for mirror in mirrors)
        report = [f"Layout check passed: {len(mirrors)} mirror(s), {unit_count} unit(s)."]
    print("\n".join(report))  # noqa: T201 (a script reports on stdout and stderr)

    return EXIT_VIOLATIONS if violations else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

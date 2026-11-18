# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Guard rail that requires file and directory names to consist of letters, digits and `_`, and to separate their words by `_`.

A name is an optional leading `.`, which hides a file such as `.gitignore`, a stem of ASCII letters, digits and `_`, and an
optional extension: a `.` followed by ASCII letters, digits and `_`. So a name contains no `-`, no space and at most one other `.`.

A separator is a run of underscores between two letters or digits. It is a single `_`; in a name that starts with `test_` it may
also be a triple `___`, which separates a module from an aspect in `test_x___<aspect>.py`. Underscores at the start or the end of
a word, as in `__init__.py`, separate no words and are left alone.

The check looks at names only. Whether a test file belongs to a module is checked by `tools/check_layout.py`.

The files are those that git tracks or would track: `git ls-files --cached --others --exclude-standard`. A directory exists when
it holds such a file.

Run `python -m tools.check_names` locally, or `python -m tools.check_names --check` as CI does; both report and neither writes.
"""

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from tools.shared.repository_files import list_files, with_directories

ROOT = Path(__file__).resolve().parents[1]

SHAPE = re.compile(r"\.?[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)?")
SEPARATOR = re.compile(r"(?<=[A-Za-z0-9])_+(?=[A-Za-z0-9])")
TEST_PREFIX = "test_"

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_TOOL_FAILURE = 2


@dataclass(frozen=True)
class Violation:
    """A path whose name breaks the naming rule, and why."""

    path: str
    reason: str

    def describe(self) -> str:
        """Return one line naming the path and what is wrong with it."""
        return f"{self.path}: {self.reason}"


def check_name(name: str) -> str | None:
    """Return why `name` breaks the naming rule, or None when it does not."""
    if SHAPE.fullmatch(name) is None:
        return "is not an optional `.`, letters, digits and `_`, and an optional `.` with an extension"
    allowed = {"_", "___"} if name.startswith(TEST_PREFIX) else {"_"}
    for separator in SEPARATOR.findall(name):
        if separator not in allowed:
            if separator == "___":
                return f"separates words by `___`, which only a name that starts with `{TEST_PREFIX}` may do"
            return f"separates words by `{separator}`; use `_`"
    return None


def find_violations(files: Iterable[str]) -> list[Violation]:
    """Return the files among `files` and their directories whose names break the naming rule, ordered by path."""
    violations: list[Violation] = []
    for path in sorted(with_directories(files)):
        reason = check_name(path.rstrip("/").rsplit("/", 1)[-1])
        if reason is not None:
            violations.append(Violation(path, reason))
    return violations


def main(argv: list[str] | None = None) -> int:
    """Report the file and directory names that break the naming rule, and fail on any of them."""
    parser = argparse.ArgumentParser(description="Check that file and directory names follow the naming rule.")
    # --check mirrors tools/lint_budget.py; this check never writes, so it only documents the CI invocation.
    parser.add_argument("--check", action="store_true", help="only report, never write (used by CI; this check never writes)")
    parser.parse_args(argv)

    try:
        files = list_files(ROOT)
    except (OSError, RuntimeError, UnicodeDecodeError) as error:
        print(f"Could not check the names in {ROOT}: {error}", file=sys.stderr)  # noqa: T201 (a script reports on stdout and stderr)
        return EXIT_TOOL_FAILURE
    violations = find_violations(files)

    if violations:
        report = ["These names break the naming rule:"]
        report += [f"  {violation.describe()}" for violation in violations]
        report.append("\nRename them; see docs/developer/tools/check_names.md.")
    else:
        report = [f"Name check passed: {len(with_directories(files))} file and directory name(s)."]
    print("\n".join(report))  # noqa: T201 (a script reports on stdout and stderr)

    return EXIT_VIOLATIONS if violations else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Guard rail that requires every text file in the repository to be stored with LF line endings.

`.gitattributes` makes git convert CRLF to LF whenever a text file is committed, so on its own it
already keeps the repository consistent. This check is the backstop for what the attribute cannot
see: a commit made before the attribute existed, for example on a long-lived branch, and an edit
of `.gitattributes` that weakens or removes the rule.

The check asks `git ls-files --eol` for the line endings git stored in the index and fails on any
text file stored with CRLF, or with a mix of LF and CRLF. The working tree is not checked: git
converts it on every commit, and an old clone may still hold CRLF files that git does not commit.

A file whose attributes say `-text`, as `binary` does, is exempt: git stores its bytes verbatim,
which is how a fixture that must keep CRLF is committed deliberately.

Run `python -m tools.check_line_endings` locally, or `python -m tools.check_line_endings --check`
as CI does; both report and neither writes.
"""

import argparse
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The line endings `git ls-files --eol` reports in the index that this repository does not allow.
FORBIDDEN_LINE_ENDINGS: dict[str, str] = {
    "crlf": "stored with CRLF line endings",
    "mixed": "stored with a mix of LF and CRLF line endings",
}

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_TOOL_FAILURE = 2


@dataclass(frozen=True)
class TrackedFile:
    """One record of `git ls-files --eol`: the line endings of a file in the index and its attributes."""

    path: str
    index_eol: str
    attributes: tuple[str, ...]

    @property
    def is_exempt(self) -> bool:
        """Return whether git stores the file verbatim, because its attributes switch the text conversion off."""
        return "-text" in self.attributes


@dataclass(frozen=True)
class Violation:
    """A tracked text file that git stores with line endings other than LF."""

    path: str
    reason: str

    def describe(self) -> str:
        """Return one line naming the file and what is wrong with it."""
        return f"{self.path}: {self.reason}"


def parse_ls_files_eol(output: str) -> list[TrackedFile]:
    """Parse the NUL-separated output of `git ls-files --eol -z`."""
    files: list[TrackedFile] = []
    for record in output.split("\0"):
        if not record:
            continue
        # Each record is `i/<eol> w/<eol> attr/<attributes>`, a TAB, and the path; the attributes may contain spaces.
        info, path = record.split("\t", 1)
        index_field, _worktree_field, attribute_field = info.split(maxsplit=2)
        files.append(
            TrackedFile(
                path=path,
                index_eol=index_field.removeprefix("i/"),
                attributes=tuple(attribute_field.removeprefix("attr/").split()),
            )
        )
    return files


def list_tracked_files(root: Path) -> list[TrackedFile]:
    """Return the files git tracks in `root` with their line endings, or raise when git is unavailable or fails."""
    git = shutil.which("git")
    if git is None:
        message = "git was not found on PATH, so the tracked files cannot be listed"
        raise RuntimeError(message)
    result = subprocess.run([git, "ls-files", "--eol", "-z"], capture_output=True, cwd=root, check=False)  # noqa: S603 (command built from constants here)
    if result.returncode != 0:
        message = f"git ls-files failed (exit code {result.returncode}):\n{result.stderr.decode('utf-8', 'replace').strip()}"
        raise RuntimeError(message)
    return parse_ls_files_eol(result.stdout.decode("utf-8"))


def find_violations(files: Iterable[TrackedFile]) -> list[Violation]:
    """Return the text files among `files` that are not stored with LF, ordered by path."""
    return [
        Violation(path=file.path, reason=FORBIDDEN_LINE_ENDINGS[file.index_eol])
        for file in sorted(files, key=lambda file: file.path)
        if file.index_eol in FORBIDDEN_LINE_ENDINGS and not file.is_exempt
    ]


def main(argv: list[str] | None = None) -> int:
    """Report the tracked text files that are not stored with LF and fail on any of them."""
    parser = argparse.ArgumentParser(description="Check that every text file tracked by git is stored with LF line endings.")
    # --check mirrors tools/lint_budget.py; this check never writes, so it only documents the CI invocation.
    parser.add_argument("--check", action="store_true", help="only report, never write (used by CI; this check never writes)")
    parser.parse_args(argv)

    try:
        files = list_tracked_files(ROOT)
    except (OSError, RuntimeError, UnicodeDecodeError, ValueError) as error:
        print(f"Could not check the files in {ROOT}: {error}", file=sys.stderr)  # noqa: T201 (a script reports on stdout and stderr)
        return EXIT_TOOL_FAILURE
    violations = find_violations(files)

    if violations:
        report = ["These files are not stored with LF line endings:"]
        report += [f"  {violation.describe()}" for violation in violations]
        report.append("\nRun `git add --renormalize .` and commit; see docs/developer/tools/check-line-endings.md.")
    else:
        report = [f"Line ending check passed: {len(files)} tracked file(s), all text files stored with LF."]
    print("\n".join(report))  # noqa: T201 (a script reports on stdout and stderr)

    return EXIT_VIOLATIONS if violations else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Guard rail that requires every text file in the repository to be UTF-8 without a byte order mark.

One encoding for the whole repository keeps the sources readable on every platform: Windows still
decodes with the ANSI code page by default, so a file written as Latin-1 or UTF-16 silently becomes
mojibake, breaks `ruff`, `pyright`, `mkdocs` or a parser test, and produces a diff full of unrelated
changes the first time somebody saves it again.

A byte order mark is rejected as well. It is valid UTF-8, but it is not stripped by `encoding="utf-8"`,
so it turns up as a stray U+FEFF character at the start of the first token, in a shebang, in a YAML
document or in a Markdown heading.

The files to check are the ones `git` tracks; generated and ignored files are therefore left alone.
Files that `git` treats as binary (they contain a NUL byte) are skipped, because they have no encoding.

Run `python tools/check_encoding.py` locally, or `python tools/check_encoding.py --check` as CI does;
both report and neither writes.
"""

import argparse
import codecs
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Only the first block is inspected for a NUL byte, which is how git itself decides a blob is binary.
BINARY_SNIFF_BYTES = 8000

# A UTF-8 BOM is valid UTF-8 and must be reported separately; the others cannot decode as UTF-8 anyway,
# but are named explicitly so the report says what the file is instead of where decoding failed.
BYTE_ORDER_MARKS: tuple[tuple[bytes, str], ...] = (
    (codecs.BOM_UTF32_LE, "UTF-32 LE"),
    (codecs.BOM_UTF32_BE, "UTF-32 BE"),
    (codecs.BOM_UTF8, "UTF-8"),
    (codecs.BOM_UTF16_LE, "UTF-16 LE"),
    (codecs.BOM_UTF16_BE, "UTF-16 BE"),
)

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_TOOL_FAILURE = 2


@dataclass(frozen=True)
class Violation:
    """A tracked file that is not UTF-8, or that is UTF-8 but starts with a byte order mark."""

    path: Path
    reason: str

    def describe(self, root: Path) -> str:
        """Return one line naming the file relative to `root` and what is wrong with it."""
        return f"{self.path.relative_to(root)}: {self.reason}"


def is_binary(data: bytes) -> bool:
    """Return whether `data` has no encoding to check, using the NUL-byte heuristic git uses."""
    return b"\x00" in data[:BINARY_SNIFF_BYTES]


def encoding_problem(data: bytes) -> str | None:
    """Return what is wrong with the encoding of `data`, or None when it is UTF-8 without a byte order mark."""
    for mark, name in BYTE_ORDER_MARKS:
        if data.startswith(mark):
            return f"starts with a {name} byte order mark"
    if is_binary(data):
        return None
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as error:
        return f"not valid UTF-8: byte 0x{data[error.start]:02x} at offset {error.start} ({error.reason})"
    return None


def tracked_files(root: Path) -> list[Path]:
    """Return the files git tracks in `root`, or raise when git is unavailable or fails."""
    git = shutil.which("git")
    if git is None:
        message = "git was not found on PATH, so the tracked files cannot be listed"
        raise RuntimeError(message)
    # -z keeps paths with non-ASCII or unusual characters intact, which --quote would otherwise escape.
    result = subprocess.run([git, "ls-files", "-z"], capture_output=True, cwd=root, check=False)  # noqa: S603 (command built from constants here)
    if result.returncode != 0:
        message = f"git ls-files failed (exit code {result.returncode}):\n{result.stderr.decode('utf-8', 'replace').strip()}"
        raise RuntimeError(message)
    names = result.stdout.decode("utf-8").split("\0")
    return [root / name for name in names if name]


def find_violations(paths: Iterable[Path]) -> list[Violation]:
    """Return the encoding violations among `paths`, ordered by path."""
    violations: list[Violation] = []
    for path in sorted(paths):
        # A tracked path can be absent from the working tree, for example during a merge or a sparse checkout.
        if not path.is_file():
            continue
        reason = encoding_problem(path.read_bytes())
        if reason is not None:
            violations.append(Violation(path=path, reason=reason))
    return violations


def main(argv: list[str] | None = None) -> int:
    """Report the tracked files that are not UTF-8 and fail on any of them."""
    parser = argparse.ArgumentParser(description="Check that every text file tracked by git is UTF-8 without a byte order mark.")
    # --check mirrors tools/lint_budget.py; this check never writes, so it only documents the CI invocation.
    parser.add_argument("--check", action="store_true", help="only report, never write (used by CI; this check never writes)")
    parser.parse_args(argv)

    try:
        paths = tracked_files(ROOT)
        violations = find_violations(paths)
    except (OSError, RuntimeError, UnicodeDecodeError) as error:
        print(f"Could not check the files in {ROOT}: {error}", file=sys.stderr)  # noqa: T201 (a script reports on stdout and stderr)
        return EXIT_TOOL_FAILURE

    if violations:
        report = ["These files are not UTF-8 encoded:"]
        report += [f"  {violation.describe(ROOT)}" for violation in violations]
        report.append("\nRe-save each file as UTF-8 without a byte order mark; see docs/developer/tools/check-encoding.md.")
    else:
        report = [f"Encoding check passed: {len(paths)} tracked file(s), all UTF-8."]
    print("\n".join(report))  # noqa: T201 (a script reports on stdout and stderr)

    return EXIT_VIOLATIONS if violations else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

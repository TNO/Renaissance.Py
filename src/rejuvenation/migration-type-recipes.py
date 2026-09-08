"""Friendly CLI to run TypeVarCheck and TypeVarTupleCheck (TypeVar/ParamSpec/TypeVarTuple modernization).

Replaces the raw `python cli.py refactor TypeVarCheck <file>` positional-argv dispatch with a
real CLI: `--help`, named flags, a dry-run-by-default safety net, and a report distinguishing
files it modified from files with TypeVars it found but couldn't safely convert.

Examples:
    python src/rejuvenation/migration-type-recipes.py ./some_repo --report review.md
    python src/rejuvenation/migration-type-recipes.py ./some_repo/file.py --apply

"""

# A CLI's entire job is printing its report to the user - this mirrors the existing
# print()+termcolor convention already used by PythonRefactoring.process().
# ruff: noqa: T201

import argparse
import difflib
import textwrap
from collections.abc import Sequence  # noqa: TC003
from dataclasses import dataclass
from pathlib import Path

from termcolor import colored

from renaissance.recipes.type_var_check import TypeVarCheck
from renaissance.recipes.type_var_tuple_check import TypeVarTupleCheck

_MAJOR_MINOR_PART_COUNT = 2

# TODO: incomplete list, extend this list with more files/directories that should always be ignored
EXCLUDED_DIRS = frozenset({".git", "__pycache__", ".venv", "venv"})


@dataclass
class FileReport:
    """Outcome of running TypeVarCheck against a single file."""

    path: Path
    result: dict[str, dict[str, str]] | None
    error: str | None
    diff: str | None


def discover_files(target: Path) -> list[Path]:
    """Return every .py file under `target`, sorted, excluding EXCLUDED_DIRS.

    Deliberately not using renaissance.project.project_scanner.PythonScanner: its package_dirs
    allowlist (["src", "lib", "test"]) assumes Renaissance.Py's own layout and would silently
    skip real third-party layouts, e.g. redis-py's source living in redis/ rather than src/. A
    migration target here is an arbitrary external codebase, not this repo.
    """
    if target.is_file():
        return [target]
    candidates = target.rglob("*.py")
    files = [path for path in candidates if not any(part in EXCLUDED_DIRS for part in path.parts)]
    return sorted(files)


def _parse_min_python(text: str) -> tuple[int, int]:
    """Parse a "MAJOR.MINOR" string into a (major, minor) tuple for argparse's type=.

    Raises argparse.ArgumentTypeError on anything else, so argparse reports a clean usage error
    instead of a raw traceback.
    """
    parts = text.split(".")
    if len(parts) != _MAJOR_MINOR_PART_COUNT or not all(part.isdigit() for part in parts):
        message = f"expected MAJOR.MINOR (e.g. 3.12), got {text!r}"
        raise argparse.ArgumentTypeError(message)
    return (int(parts[0]), int(parts[1]))


def has_fixed(report: FileReport) -> bool:
    """Return True if any phase of report.result fixed at least one name."""
    if report.result is None:
        return False
    return any("fixed" in phase.values() for phase in report.result.values())


def has_unsafe(report: FileReport) -> bool:
    """Return True if any phase of report.result left at least one name unsafe to touch."""
    if report.result is None:
        return False
    return any("unsafe" in phase.values() for phase in report.result.values())


def is_clean(report: FileReport) -> bool:
    """Return True if report.result found no TypeVar/ParamSpec/TypeVarTuple usage at all."""
    if report.result is None:
        return False
    return not any(phase for phase in report.result.values())


def _unified_diff(before: str, after: str, path: Path) -> str | None:
    """Return a unified diff between `before` and `after`, or None if they're identical."""
    if before == after:
        return None
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
        ),
    )


def process_file(path: Path, *, apply: bool, min_python: tuple[int, int] | None) -> FileReport:
    """Run TypeVarTupleCheck then TypeVarCheck against a single file, returning one FileReport.

    TypeVarTupleCheck runs first deliberately: TypeVarCheck's own PEP 695 conversion removes a
    TypeVarTuple's module-level declaration once it converts it, and TypeVarTupleCheck can only
    find an `Unpack[T]` usage while that declaration still exists - running TypeVarCheck first
    would make TypeVarTupleCheck blind to exactly the case that most needs it. Any failure is
    caught and reported on FileReport.error instead of propagating, since one bad file must never
    abort a batch run.
    """
    try:
        before = path.read_text(encoding="utf-8")  # read before constructing either recipe, so this is guaranteed untouched

        tvt_recipe = TypeVarTupleCheck(path)
        tvt_recipe.in_memory = not apply  # dry run: commit() rebuilds in memory instead of writing to disk
        if min_python is not None:
            tvt_recipe.min_python_override = min_python
        tvt_recipe.run()

        tv_recipe = TypeVarCheck(path)
        tv_recipe.in_memory = not apply
        if min_python is not None:
            tv_recipe.min_python_override = min_python
        tv_recipe.run()

        result = dict(tv_recipe.result)
        result["unpack_syntax"] = tvt_recipe.result
        diff = _combined_diff(before, path, apply=apply, tvt_recipe=tvt_recipe, tv_recipe=tv_recipe)
    except Exception as exc:  # noqa: BLE001 - isolate one bad file, never abort the whole batch
        return FileReport(path=path, result=None, error=f"{type(exc).__name__}: {exc}", diff=None)
    return FileReport(path=path, result=result, error=None, diff=diff)


def _combined_diff(
    before: str,
    path: Path,
    *,
    apply: bool,
    tvt_recipe: TypeVarTupleCheck,
    tv_recipe: TypeVarCheck,
) -> str | None:
    """Build the diff for a file processed by both recipes.

    In --apply mode both recipes already wrote for real, chained through the filesystem (
    TypeVarCheck reads the file TypeVarTupleCheck already updated), so re-reading `path` once gives
    one accurate, unified diff. In dry-run mode neither recipe's in-memory preview can be fed into
    the other's constructor (PythonRefactoring only reads from a real file path), so each recipe's
    own preview is diffed independently against the same original `before` and concatenated, each
    labeled with which recipe produced it so the two previews aren't visually ambiguous together.
    """
    if apply:
        after = path.read_text(encoding="utf-8")
        return _unified_diff(before, after, path)

    labeled_diffs = (
        (label, _unified_diff(before, recipe.apply_to_string(), path))
        for label, recipe in (("TypeVarTupleCheck", tvt_recipe), ("TypeVarCheck", tv_recipe))
    )
    parts = [f"[{label}]\n{diff}" for label, diff in labeled_diffs if diff]
    return "\n".join(parts) or None


def _format_commit_summary(reports: list[FileReport], *, apply: bool) -> str:
    """Build the short, copy-pasteable commit-message-style summary."""
    modified = sum(1 for report in reports if has_fixed(report))
    needs_review = sum(1 for report in reports if has_unsafe(report))
    clean = sum(1 for report in reports if is_clean(report))
    errors = sum(1 for report in reports if report.error is not None)
    mode_note = "" if apply else " (dry run - nothing written)"
    return (
        "Modernize TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax\n\n"
        f"{modified} files modified, {needs_review} need manual review, {clean} clean, "
        f"{errors} errors (of {len(reports)} processed){mode_note}"
    )


def _format_console_report(reports: list[FileReport], *, apply: bool, show_diff: bool) -> str:
    """Build the full per-file report: MODIFIED / NEEDS MANUAL REVIEW / ERRORS sections.

    Clean files (no TypeVar usage found at all) are folded into the top-line count only, never
    listed individually - the report's job is to surface what needs attention.
    """
    modified = [report for report in reports if has_fixed(report)]
    needs_review = [report for report in reports if has_unsafe(report)]
    errors = [report for report in reports if report.error is not None]
    clean_count = sum(1 for report in reports if is_clean(report))
    mode = "APPLIED" if apply else "DRY RUN (no files written)"

    lines = [
        "Renaissance TypeVarCheck migration report",
        f"Mode: {mode}",
        f"Processed {len(reports)} files: {len(modified)} modified, {len(needs_review)} need "
        f"manual review, {clean_count} clean, {len(errors)} errors",
        "",
        f"MODIFIED ({len(modified)})",
    ]
    for report in modified:
        lines.append(f"  {report.path}")
        for phase, names in (report.result or {}).items():
            fixed = [name for name, status in names.items() if status == "fixed"]
            if fixed:
                lines.append(f"    {phase}: {', '.join(fixed)}")
        if show_diff and report.diff:
            lines.append(report.diff)

    lines.extend(["", f"NEEDS MANUAL REVIEW ({len(needs_review)})"])
    for report in needs_review:
        lines.append(f"  {report.path}")
        for phase, names in (report.result or {}).items():
            unsafe = [name for name, status in names.items() if status == "unsafe"]
            if unsafe:
                lines.append(f"    {phase}: {', '.join(unsafe)}")

    lines.extend(["", f"ERRORS ({len(errors)})"])
    lines.extend(f"  {report.path}: {report.error}" for report in errors)

    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for this CLI's --help/usage text and flags."""
    parser = argparse.ArgumentParser(
        prog="migration-type-recipes.py",
        description="Modernize legacy TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax.",
        epilog=textwrap.dedent("""\
            Examples:
              python src/rejuvenation/migration-type-recipes.py ./some_repo --report review.md
              python src/rejuvenation/migration-type-recipes.py ./some_repo/file.py --apply
            """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="A .py file or a directory to scan.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to disk. Without this flag, nothing is written (dry run/preview only).",
    )
    parser.add_argument(
        "--min-python",
        type=_parse_min_python,
        metavar="MAJOR.MINOR",
        help="Override the detected minimum target Python version, e.g. 3.12 - PEP 695 syntax "
        "requires 3.12+, and without this flag it's detected from the target's pyproject.toml.",
    )
    parser.add_argument("--report", type=Path, metavar="PATH", help="Also write the full report to this file.")
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show unified diffs for modified files even with --apply (dry run always shows them).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, run TypeVarCheck across the target, print/save the report, return an exit code.

    Exit codes: 0 on normal completion (files needing manual review are informational, not a
    failure), 2 on a usage error (bad path/argument), 3 if any file hit an unhandled exception.
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    target: Path = args.path
    if not target.exists():
        parser.error(f"path does not exist: {target}")
    if target.is_file() and target.suffix != ".py":
        parser.error(f"not a Python file: {target}")

    files = discover_files(target)
    reports = [process_file(path, apply=args.apply, min_python=args.min_python) for path in files]

    show_diff = args.diff or not args.apply
    console_report = _format_console_report(reports, apply=args.apply, show_diff=show_diff)
    print(console_report)
    print()
    print(colored(_format_commit_summary(reports, apply=args.apply), "green", attrs=["bold"]))

    if args.report is not None:
        args.report.write_text(console_report, encoding="utf-8")

    return 3 if any(report.error is not None for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())

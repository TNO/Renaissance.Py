"""Friendly CLI to run TypeVarTupleCheck and TypeVarCheck (TypeVar/ParamSpec/TypeVarTuple modernization).

Replaces the raw `python cli.py refactor TypeVarCheck <file>` positional-argv dispatch with a
real CLI: `--help`, named flags, and a report distinguishing files it modified from files with
TypeVars it found but couldn't safely convert.

Examples:
    python src/rejuvenation/migration-type-recipes.py ./some_repo --report review.md
    python src/rejuvenation/migration-type-recipes.py ./some_repo/file.py

"""

# A CLI's entire job is printing its report to the user - this mirrors the existing
# print()+termcolor convention already used by PythonRefactoring.process().
# ruff: noqa: T201

import argparse
import subprocess
import sys
import textwrap
from collections.abc import Sequence  # noqa: TC003
from dataclasses import dataclass
from pathlib import Path

from termcolor import colored

from renaissance.recipes.step_runner import Step, run_steps
from renaissance.recipes.type_var_check import TypeVarCheck
from renaissance.recipes.type_var_domain import UNSAFE_RULES, UnsafeReason, doc_link
from renaissance.recipes.type_var_tuple_check import TypeVarTupleCheck

_MAJOR_MINOR_PART_COUNT = 2

# TODO: incomplete list, extend this list with more files/directories that should always be ignored
EXCLUDED_DIRS = frozenset({".git", "__pycache__", ".venv", "venv"})


@dataclass
class FileReport:
    """Outcome of running TypeVarTupleCheck and TypeVarCheck against a single file."""

    path: Path
    result: dict[str, dict[str, str]] | None
    error: str | None
    reasons: dict[str, dict[str, UnsafeReason]] | None = None


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


def process_file(path: Path, *, min_python: tuple[int, int] | None) -> FileReport:
    """Run TypeVarTupleCheck then TypeVarCheck's phases against a single file, returning one FileReport.

    TypeVarTupleCheck runs first: TypeVarCheck's own PEP 695 conversion removes a TypeVarTuple's
    module-level declaration once it converts it, and TypeVarTupleCheck can only find an
    `Unpack[T]` usage while that declaration still exists. Any failure is caught and reported on
    FileReport.error instead of propagating, since one bad file must never abort a batch run.
    """
    try:
        tvt_recipe = TypeVarTupleCheck(path)
        if min_python is not None:
            tvt_recipe.min_python_override = min_python
        unpack_result = run_steps([Step("unpack_syntax", tvt_recipe, tvt_recipe.fix_legacy_unpack_usage)])

        # TypeVarCheck is constructed only now, not upfront alongside tvt_recipe: each recipe reads
        # `path` from disk once, at construction, and never again - constructing it earlier would
        # give it a stale in-memory copy from before TypeVarTupleCheck's step wrote to disk, and its
        # own commit() would then overwrite that fix with its own reconstruction of the old content.
        tv_recipe = TypeVarCheck(path)
        if min_python is not None:
            tv_recipe.min_python_override = min_python
        typevar_result = run_steps(
            [
                Step("cross_file", tv_recipe, tv_recipe.localize_imported_typevars),
                Step("converted", tv_recipe, tv_recipe.convert_declared_typevars),
                Step("orphaned", tv_recipe, tv_recipe.remove_orphaned_declarations),
            ],
        )

        result = {**unpack_result, **typevar_result}
        reasons = {
            "unpack_syntax": tvt_recipe.unsafe_reasons,
            "cross_file": tv_recipe.cross_file_unsafe_reasons,
            "converted": tv_recipe.converted_unsafe_reasons,
            "orphaned": tv_recipe.orphaned_unsafe_reasons,
        }
    except Exception as exc:  # noqa: BLE001 - isolate one bad file, never abort the whole batch
        return FileReport(path=path, result=None, error=f"{type(exc).__name__}: {exc}")
    return FileReport(path=path, result=result, error=None, reasons=reasons)


def _run_ruff_unused_import_cleanup(paths: list[Path]) -> None:
    """Run `ruff check --fix --select F401` over every path, dropping any now-unused import.

    Best-effort: prints a warning and returns normally if ruff can't be invoked (e.g. not
    installed), rather than raising - the files' own content is already correct at this point
    regardless of whether this cleanup succeeds.
    """
    try:
        subprocess.run(  # noqa: S603 - fixed argv list (sys.executable + literals + our own discovered paths), no shell
            [sys.executable, "-m", "ruff", "check", "--fix", "--select", "F401", *(str(path) for path in paths)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(colored(f"warning: could not run ruff for import cleanup: {exc}", "yellow"))


def _format_commit_summary(reports: list[FileReport]) -> str:
    """Build the short, copy-pasteable commit-message-style summary."""
    modified = sum(1 for report in reports if has_fixed(report))
    needs_review = sum(1 for report in reports if has_unsafe(report))
    clean = sum(1 for report in reports if is_clean(report))
    errors = sum(1 for report in reports if report.error is not None)
    return (
        "Modernize TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax\n\n"
        f"{modified} files modified, {needs_review} need manual review, {clean} clean, "
        f"{errors} errors (of {len(reports)} processed)"
    )


def _format_console_report(reports: list[FileReport]) -> str:
    """Build the full per-file report: MODIFIED / NEEDS MANUAL REVIEW / ERRORS sections.

    Clean files (no TypeVar usage found at all) are folded into the top-line count only, never
    listed individually - the report's job is to surface what needs attention.
    """
    modified = [report for report in reports if has_fixed(report)]
    needs_review = [report for report in reports if has_unsafe(report)]
    errors = [report for report in reports if report.error is not None]
    clean_count = sum(1 for report in reports if is_clean(report))

    lines = [
        "Renaissance TypeVarCheck migration report",
        (f"Processed {len(reports)} files: {len(modified)} modified, {len(needs_review)} need "
        f"manual review, {clean_count} clean, {len(errors)} errors"),
    ]
    if modified:
        lines.append(
            "Unused imports across the modified files above were also cleaned up via `ruff check --fix --select F401`.",
        )
    lines.extend(["", f"MODIFIED ({len(modified)})"])
    for report in modified:
        lines.append(f"  {report.path}")
        for phase, names in (report.result or {}).items():
            fixed = [name for name, status in names.items() if status == "fixed"]
            if fixed:
                lines.append(f"    {phase}: {', '.join(fixed)}")

    lines.extend(["", f"NEEDS MANUAL REVIEW ({len(needs_review)})"])
    for report in needs_review:
        lines.append(f"  {report.path}")
        for phase, names in (report.result or {}).items():
            phase_reasons = (report.reasons or {}).get(phase, {})
            unsafe = [name for name, status in names.items() if status == "unsafe"]
            if unsafe:
                lines.append(f"    {phase}: {', '.join(unsafe)}")
            for name in unsafe:
                reason = phase_reasons.get(name)
                if reason is not None:
                    lines.append(f"      {name}: {UNSAFE_RULES[reason].message} -> {doc_link(reason)}")

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
              python src/rejuvenation/migration-type-recipes.py ./some_repo/file.py
            """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="A .py file or a directory to scan.")
    parser.add_argument(
        "--min-python",
        type=_parse_min_python,
        metavar="MAJOR.MINOR",
        help="Override the detected minimum target Python version, e.g. 3.12 - PEP 695 syntax "
        "requires 3.12+, and without this flag it's detected from the target's pyproject.toml.",
    )
    parser.add_argument("--report", type=Path, metavar="PATH", help="Also write the full report to this file.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, run the recipes across the target, print/save the report, return an exit code.

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
    reports = [process_file(path, min_python=args.min_python) for path in files]

    modified_paths = [report.path for report in reports if has_fixed(report)]
    if modified_paths:
        _run_ruff_unused_import_cleanup(modified_paths)

    console_report = _format_console_report(reports)
    print(console_report)
    print()
    print(colored(_format_commit_summary(reports), "green", attrs=["bold"]))

    if args.report is not None:
        args.report.write_text(console_report, encoding="utf-8")

    return 3 if any(report.error is not None for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())

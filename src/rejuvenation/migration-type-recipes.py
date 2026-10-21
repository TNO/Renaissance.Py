# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""CLI that modernizes type parameters (TypeVar, ParamSpec, TypeVarTuple) to PEP 695 syntax.

Runs TypeParameterCheck on a file or directory, and reports which files were modified and which need
manual review.

Example:
    python src/rejuvenation/migration-type-recipes.py ./repo --py 3.12 --report review.md --ignore folder/types.py

"""

# Printing the report is this CLI's purpose.
# ruff: noqa: T201

import argparse
import subprocess
import sys
import textwrap
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from termcolor import colored

from renaissance.project.project_scanner import PythonScanner
from renaissance.recipes.type_parameter_check import MIN_SUPPORTED_PYTHON, TypeParameterCheck
from renaissance.recipes.type_parameter_rules import DOCS_BASE_URL, UNSAFE_RULES, UnsafeReason
from renaissance.utils.import_resolution import collect_project_imported_names

_MAJOR_MINOR_PART_COUNT = 2
_TYPE_PARAM_KINDS = ("TypeVar", "ParamSpec", "TypeVarTuple")
_FIXED_DESCRIPTIONS = {
    "converted": "converted to PEP 695 in functions",
    "orphaned": "unused declaration removed",
    "cross_file": "import replaced by a local declaration",
}
_MAX_LISTED_NAMES = 10


@dataclass
class FileReport:
    """Outcome of running TypeParameterCheck against a single file."""

    path: Path
    result: dict[str, dict[str, str]] | None
    error: str | None
    reasons: dict[str, dict[str, UnsafeReason]] | None = None
    kinds: dict[str, str] | None = None
    ignored: frozenset[str] = frozenset()


@dataclass
class KindCount:
    """How many type parameters of one kind a run reported, and how many were fixed, need manual review or were ignored."""

    reported: int = 0
    fixed: int = 0
    needs_review: int = 0
    ignored: int = 0


@dataclass(frozen=True)
class LocalizationSettings:
    """Whether imported type parameters are copied into the importing file, and the files they are never copied from."""

    enabled: bool = True
    ignored_files: frozenset[Path] = frozenset()


_DEFAULT_LOCALIZATION = LocalizationSettings()


def resolve_target_files(target: Path) -> list[Path]:
    """Return the .py files to process for `target`.

    A single .py file is returned as-is; a directory is scanned recursively with PythonScanner over
    the whole tree (no package_dirs allowlist), so any project layout works.
    """
    if target.is_file():
        return [target]
    return [Path(path) for path in PythonScanner(str(target)).find_sources()]


def _parse_py_version(text: str) -> tuple[int, int]:
    """Parse a "MAJOR.MINOR" string into a (major, minor) tuple for argparse's type=.

    Raises:
        argparse.ArgumentTypeError: If text is not in MAJOR.MINOR form or is below MIN_SUPPORTED_PYTHON.

    """
    parts = text.split(".")
    if len(parts) != _MAJOR_MINOR_PART_COUNT or not all(part.isdigit() for part in parts):
        message = f"expected MAJOR.MINOR (e.g. 3.12), got {text!r}"
        raise argparse.ArgumentTypeError(message)
    version = (int(parts[0]), int(parts[1]))
    if version < MIN_SUPPORTED_PYTHON:
        minimum = ".".join(map(str, MIN_SUPPORTED_PYTHON))
        message = f"expected {minimum} or higher, since PEP 695 syntax does not exist below it, got {text!r}"
        raise argparse.ArgumentTypeError(message)
    return version


def has_fixed(report: FileReport) -> bool:
    """Return True if any phase of report.result fixed at least one name."""
    if report.result is None:
        return False
    return any("fixed" in phase.values() for phase in report.result.values())


def has_unsafe(report: FileReport) -> bool:
    """Return True if any phase of report.result gave at least one name a reason to review."""
    return any(report.reasons.values()) if report.reasons else False


def is_clean(report: FileReport) -> bool:
    """Return True if report.result found no type parameter usage at all."""
    if report.result is None:
        return False
    return not any(phase for phase in report.result.values())


def process_file(
    path: Path,
    *,
    min_python: tuple[int, int],
    project_root: Path,
    project_wide_imported_names: frozenset[str],
    localization: LocalizationSettings = _DEFAULT_LOCALIZATION,
) -> FileReport:
    """Run TypeParameterCheck's three phases on one file and return its FileReport.

    Any exception is caught and stored on FileReport.error, so one bad file never aborts a batch run.
    """
    try:
        recipe = TypeParameterCheck(path)
        recipe.min_python = min_python
        recipe.project_root = project_root
        recipe.project_wide_imported_names = project_wide_imported_names
        recipe.ignore_localize_origins = localization.ignored_files
        recipe.localize_imports = localization.enabled
        result = recipe.check()
        reasons = {
            "cross_file": recipe.cross_file_unsafe_reasons,
            "converted": recipe.converted_unsafe_reasons,
            "orphaned": recipe.orphaned_unsafe_reasons,
        }
    except Exception as exc:  # noqa: BLE001 - isolate one bad file, never abort the whole batch
        return FileReport(path=path, result=None, error=f"{type(exc).__name__}: {exc}")
    return FileReport(
        path=path,
        result=result,
        error=None,
        reasons=reasons,
        kinds=recipe.type_param_kinds,
        ignored=frozenset(recipe.ignored_names),
    )


def _merge_reports(first: FileReport, second: FileReport) -> FileReport:
    """Return the report of a file processed twice: second's names replace first's, and first's other names stay.

    A reason from first is dropped when second evaluated the same name again. A second that errored is returned as it is.
    """
    if second.error is not None or first.result is None or second.result is None:
        return second
    first_reasons = first.reasons or {}
    second_reasons = second.reasons or {}
    return FileReport(
        path=first.path,
        result={phase: {**names, **second.result.get(phase, {})} for phase, names in first.result.items()},
        error=None,
        reasons={
            phase: {name: reason for name, reason in reasons.items() if name not in second.result.get(phase, {})}
            | second_reasons.get(phase, {})
            for phase, reasons in first_reasons.items()
        },
        kinds={**(first.kinds or {}), **(second.kinds or {})},
        ignored=first.ignored | second.ignored,
    )


def _run_second_pass(
    reports: list[FileReport],
    files: Sequence[Path],
    project_root: Path,
    min_python: tuple[int, int],
    localization: LocalizationSettings,
) -> list[FileReport]:
    """Process again the files that kept a declaration because another file imported it, and merge the two reports of each.

    The imported names are collected again, so a declaration whose importers were all localized in the first pass is
    no longer protected. Every other report is returned as it was.
    """
    candidates = {
        report.path
        for report in reports
        if any(UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT in reasons.values() for reasons in (report.reasons or {}).values())
    }
    if not candidates:
        return reports
    imported_names_by_file = collect_project_imported_names(files, project_root)
    merged: list[FileReport] = []
    for report in reports:
        if report.path not in candidates:
            merged.append(report)
            continue
        second = process_file(
            report.path,
            min_python=min_python,
            project_root=project_root,
            project_wide_imported_names=imported_names_by_file.get(report.path, frozenset()),
            localization=localization,
        )
        merged.append(_merge_reports(report, second))
        print(f"File {report.path} checked again.")
    return merged


def _run_ruff_import_cleanup(paths: list[Path]) -> None:
    """Run `ruff check --fix --select F401,I001` over every path.

    Drops any now-unused import (F401), then merges and sorts the imports (I001) under the settings ruff
    finds for each path.

    Best-effort: if ruff can't be invoked (e.g. not installed), prints a warning instead of raising.
    The files are already valid without this cleanup.
    """
    try:
        subprocess.run(  # noqa: S603 - fixed argv list (sys.executable + literals + our own discovered paths), no shell
            [sys.executable, "-m", "ruff", "check", "--fix", "--select", "F401,I001", *(str(path) for path in paths)],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        print(colored(f"warning: could not run ruff for import cleanup: {exc}", "yellow"))


def _files(count: int) -> str:
    """Return count with "file" pluralized, e.g. "1 file" or "2 files"."""
    return f"{count} file" if count == 1 else f"{count} files"


def _format_names(file_counts: Counter[str]) -> str:
    """Return the names, most files first then alphabetical, each with its file count if above one.

    Lists at most _MAX_LISTED_NAMES names and summarises the rest as "and N more".
    """
    ranked = sorted(file_counts.items(), key=lambda item: (-item[1], item[0]))
    listed = ", ".join(name if count == 1 else f"{name} ({_files(count)})" for name, count in ranked[:_MAX_LISTED_NAMES])
    hidden = len(ranked) - _MAX_LISTED_NAMES
    return f"{listed} and {hidden} more" if hidden > 0 else listed


def _format_commit_summary(reports: Sequence[FileReport], min_python: tuple[int, int]) -> str:
    """Build the copy-pasteable commit message: what was done to which names, and what is left for manual review.

    Names are grouped by action with the number of files they were fixed in. The manual review line,
    with the files needing it and their reasons by frequency, is left out when no file needs review.
    """
    modified = [report for report in reports if has_fixed(report)]
    names_by_action = {action: Counter[str]() for action in _FIXED_DESCRIPTIONS.values()}
    for report in modified:
        for name, actions in _fixed_descriptions(report).items():
            for action in actions:
                names_by_action[action][name] += 1
    version = ".".join(map(str, min_python))
    lines = [
        "Modernize TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax",
        "",
        f"Convert type parameters to PEP 695 syntax in {_files(len(modified))} (Python {version}+).",
        "",
        *(f"- {action}: {_format_names(file_counts)}" for action, file_counts in names_by_action.items() if file_counts),
    ]
    needs_review = sum(1 for report in reports if has_unsafe(report))
    if needs_review:
        reasons = ", ".join(f"{UNSAFE_RULES[reason].message} ({count})" for reason, count in rank_reasons(reports))
        lines.extend(["", f"{_files(needs_review)} left for manual review: {reasons}."])
    return "\n".join(lines)


def _name_statuses(report: FileReport) -> dict[str, str]:
    """Return {name: "fixed" | "unsafe"} over all phases of report.result; "unsafe" wins if any phase gave the name a reason."""
    statuses: dict[str, str] = {}
    for phase in (report.result or {}).values():
        for name, status in phase.items():
            if statuses.get(name) != "unsafe":
                statuses[name] = status
    for phase_reasons in (report.reasons or {}).values():
        statuses.update(dict.fromkeys(phase_reasons, "unsafe"))
    return statuses


def count_by_kind(reports: Sequence[FileReport]) -> dict[str, KindCount]:
    """Count the type parameters the reports list, per kind (TypeVar, ParamSpec, TypeVarTuple).

    A name counts once per file, as needing review if any phase left it unsafe and as fixed otherwise. A name
    the file imports from an ignored file counts as ignored. Files that errored are skipped.
    """
    counts = {kind: KindCount() for kind in _TYPE_PARAM_KINDS}
    for report in reports:
        kinds = report.kinds or {}
        for name in report.ignored:
            counts[kinds[name]].reported += 1
            counts[kinds[name]].ignored += 1
        for name, status in _name_statuses(report).items():
            count = counts[kinds[name]]
            count.reported += 1
            if status == "unsafe":
                count.needs_review += 1
            else:
                count.fixed += 1
    return counts


def rank_reasons(reports: Sequence[FileReport]) -> list[tuple[UnsafeReason, int]]:
    """Return each UnsafeReason the reports hit with its count, most common first, ties in UnsafeReason order.

    Every (phase, name) reason counts, so a name unsafe for two reasons counts under both.
    """
    counter = Counter(reason for report in reports for phase in (report.reasons or {}).values() for reason in phase.values())
    order = list(UnsafeReason)
    return sorted(counter.items(), key=lambda item: (-item[1], order.index(item[0])))


def _code(text: object) -> str:
    """Return text as a Markdown inline code span."""
    return f"`{text}`"


def _heading(text: str) -> str:
    """Return text as a bold Markdown line, used for the report's section headings."""
    return f"**{text}**"


def _table_row(cells: Sequence[str], widths: Sequence[int]) -> str:
    """Return one Markdown table row with each cell padded to its column width."""
    return "| " + " | ".join(cell.ljust(width) for cell, width in zip(cells, widths, strict=True)) + " |"


def _format_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    """Return a Markdown table as lines, with every column padded to its widest cell and the dash row to the same width."""
    widths = [max(len(cell) for cell in column) for column in zip(headers, *rows, strict=True)]
    return [_table_row(headers, widths), _table_row(["-" * width for width in widths], widths), *(_table_row(row, widths) for row in rows)]


def _summary_tables(reports: Sequence[FileReport], *, show_ignored: bool) -> list[str]:
    """Return the report's summary tables: type parameters per kind, then the unsafe reasons by frequency.

    The Ignored column is only there when show_ignored is True. The reasons table is left out when no reason was hit.
    """
    headers = ["Kind", "Reported", "Fixed", "Needs review", *(["Ignored"] if show_ignored else [])]
    kind_rows = [
        [_code(kind), str(c.reported), str(c.fixed), str(c.needs_review), *([str(c.ignored)] if show_ignored else [])]
        for kind, c in count_by_kind(reports).items()
    ]
    lines = ["", _heading("TYPE PARAMETERS BY KIND"), "", *_format_table(headers, kind_rows)]
    ranking = rank_reasons(reports)
    if ranking:
        reason_rows = [[UNSAFE_RULES[reason].message, str(count)] for reason, count in ranking]
        lines.extend(["", _heading("UNSAFE REASONS, MOST COMMON FIRST"), "", *_format_table(["Reason", "Count"], reason_rows)])
    return lines


def _join_with_blank_lines(entries: list[list[str]]) -> list[str]:
    """Flatten entries into one list of lines, with a blank line between consecutive entries."""
    lines: list[str] = []
    for index, entry in enumerate(entries):
        if index:
            lines.append("")
        lines.extend(entry)
    return lines


def _fixed_descriptions(report: FileReport) -> dict[str, list[str]]:
    """Return {name: [what was done to it]} for the names report.result fixed.

    A converted name isn't described as removed, because its declaration is always removed afterwards,
    and a removed name isn't described as localized.
    """
    result = report.result or {}
    converted = {name for name, status in result.get("converted", {}).items() if status == "fixed"}
    removed = {name for name, status in result.get("orphaned", {}).items() if status == "fixed"} - converted
    descriptions: dict[str, list[str]] = {}
    for phase, names in result.items():
        for name, status in names.items():
            if status == "fixed" and not (phase == "orphaned" and name in converted) and not (phase == "cross_file" and name in removed):
                descriptions.setdefault(name, []).append(_FIXED_DESCRIPTIONS[phase])
    return descriptions


def _modified_entry(report: FileReport, project_root: Path) -> list[str]:
    """Return the MODIFIED lines for one file: its path relative to project_root, then what was done to each name."""
    lines = [f"  {_code(report.path.relative_to(project_root))}"]
    lines.extend(f"    {_code(name)}: {', '.join(texts)}" for name, texts in _fixed_descriptions(report).items())
    return lines


def _needs_review_groups(reports: Sequence[FileReport], project_root: Path) -> list[list[str]]:
    """Return one block of NEEDS MANUAL REVIEW lines per reason, most common reason first.

    A block is the reason as a heading, then each file it applies to with the names it applies to.
    """
    names_by_reason: dict[UnsafeReason, dict[Path, list[str]]] = {}
    for report in reports:
        for phase_reasons in (report.reasons or {}).values():
            for name, reason in phase_reasons.items():
                names = names_by_reason.setdefault(reason, {}).setdefault(report.path, [])
                if name not in names:
                    names.append(name)
    groups: list[list[str]] = []
    for reason, _ in rank_reasons(reports):
        message = UNSAFE_RULES[reason].message
        files = names_by_reason[reason].items()
        groups.append(
            [
                _heading(message[:1].upper() + message[1:]),
                *(f"  {_code(path.relative_to(project_root))}: {', '.join(map(_code, names))}" for path, names in files),
            ],
        )
    return groups


def _format_console_report(
    reports: list[FileReport],
    *,
    project_root: Path,
    localization: LocalizationSettings,
) -> str:
    """Build the full report as Markdown: MODIFIED / NEEDS MANUAL REVIEW / ERRORS sections.

    Files are listed by their path relative to project_root. MODIFIED lists each file with what was done to
    its names, separated by a blank line; NEEDS MANUAL REVIEW groups the files and names by reason. Clean
    files (no type parameter usage at all) are only counted, not listed, so the report shows what needs
    attention. The IGNORED FILES section is only included when localization.ignored_files is not empty,
    and the Ignored column when it is not empty or localization is disabled.
    """
    modified = [report for report in reports if has_fixed(report)]
    needs_review = [report for report in reports if has_unsafe(report)]
    errors = [report for report in reports if report.error is not None]
    clean_count = sum(1 for report in reports if is_clean(report))

    lines = [
        "Renaissance TypeParameterCheck migration report",
        (
            f"Processed {len(reports)} files: {len(modified)} modified, {len(needs_review)} need "
            f"manual review, {clean_count} clean, {len(errors)} errors"
        ),
    ]
    if localization.ignored_files:
        lines.extend(["", _heading(f"IGNORED FILES ({len(localization.ignored_files)})")])
        lines.extend(f"  {_code(ignored.relative_to(project_root))}" for ignored in sorted(localization.ignored_files))
    lines.extend(_summary_tables(reports, show_ignored=bool(localization.ignored_files) or not localization.enabled))
    lines.extend(["", _heading(f"MODIFIED ({len(modified)})")])
    lines.extend(_join_with_blank_lines([_modified_entry(report, project_root) for report in modified]))

    lines.extend(["", _heading(f"NEEDS MANUAL REVIEW ({len(needs_review)})")])
    if needs_review:
        lines.extend([f"  {DOCS_BASE_URL}", ""])
    lines.extend(_join_with_blank_lines(_needs_review_groups(needs_review, project_root)))

    lines.extend(["", _heading(f"ERRORS ({len(errors)})")])
    lines.extend(f"  {_code(report.path.relative_to(project_root))}: {report.error}" for report in errors)

    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for this CLI's --help/usage text and flags."""
    parser = argparse.ArgumentParser(
        prog="migration-type-recipes.py",
        description="Modernize legacy TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax.",
        epilog=textwrap.dedent("""\
            Examples:
                python src/rejuvenation/migration-type-recipes.py ./repo --py 3.12 --report review.md --ignore folder/types.py
            """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", type=Path, help="A .py file or a directory to scan.")
    parser.add_argument(
        "--py",
        type=_parse_py_version,
        required=True,
        metavar="MAJOR.MINOR",
        help=("Minimum Python version the target project supports is 3.12."),
    )
    parser.add_argument("--report", type=Path, metavar="PATH", help="Also write the full report to this file.")
    parser.add_argument(
        "--no-ruff",
        action="store_true",
        help="Skip the final `ruff check --fix --select F401,I001` pass that drops imports made unused and sorts the rest.",
    )
    parser.add_argument(
        "--ignore",
        action="extend",
        nargs="+",
        type=Path,
        default=[],
        metavar="FILE",
        help=(
            "Files, relative to the scanned directory, that are left untouched; their type parameters are not copied "
            "into the files importing them, which keep those imports. Give the path argument first, since this option "
            "takes every value after it."
        ),
    )
    parser.add_argument(
        "--no-localization",
        action="store_true",
        help=(
            "Keep the imports of project type parameters instead of copying their declarations into the importing file; "
            "the functions using them are not converted."
        ),
    )
    parser.add_argument(
        "--second-pass",
        action="store_true",
        help=(
            "Process again the files that kept a declaration only because another file imported it when the run started, "
            "and report both passes together."
        ),
    )
    return parser


def _localization_settings(parser: argparse.ArgumentParser, args: argparse.Namespace, project_root: Path) -> LocalizationSettings:
    """Build the LocalizationSettings from --no-localization and --ignore, the latter resolved against project_root.

    Calls parser.error, which exits with code 2, if an --ignore file does not exist.
    """
    for ignored in args.ignore:
        if not (project_root / ignored).is_file():
            parser.error(f"--ignore: file does not exist: {ignored}")
    return LocalizationSettings(
        enabled=not args.no_localization,
        ignored_files=frozenset((project_root / ignored).resolve() for ignored in args.ignore),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, run TypeParameterCheck across the target, print/save the report, return an exit code.

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

    # Absolute and normalized, so file paths match the keys collect_project_imported_names returns.
    target = target.resolve()
    files = resolve_target_files(target)
    project_root = target if target.is_dir() else target.parent
    imported_names_by_file = collect_project_imported_names(files, project_root)

    localization = _localization_settings(parser, args, project_root)

    reports: list[FileReport] = []
    for path in files:
        if path in localization.ignored_files:
            continue
        project_wide_imported_names = imported_names_by_file.get(path, frozenset())
        report = process_file(
            path,
            min_python=args.py,
            project_root=project_root,
            project_wide_imported_names=project_wide_imported_names,
            localization=localization,
        )
        reports.append(report)
        print(f"File {path} checked.")

    if args.second_pass:
        reports = _run_second_pass(reports, files, project_root, args.py, localization)

    modified_paths = [report.path for report in reports if has_fixed(report)]
    ruff_ran = bool(modified_paths) and not args.no_ruff
    if ruff_ran:
        # TODO(FrancescoPezzella): removed statements leave their blank lines behind; ruff's E303 (preview) collapses them, but not
        #  at file start.
        #  https://github.com/TNO/Renaissance.Py/issues/279
        _run_ruff_import_cleanup(modified_paths)

    console_report = _format_console_report(
        reports,
        project_root=project_root,
        localization=localization,
    )
    print(console_report)
    if modified_paths:
        print()
        print(colored(_format_commit_summary(reports, args.py), "green", attrs=["bold"]))

    if args.report is not None:
        args.report.write_text(console_report, encoding="utf-8")

    return 3 if any(report.error is not None for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())

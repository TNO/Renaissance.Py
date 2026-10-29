# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Run ruff and pyright with every check enabled, and count their issues per kind.

`tools/lint_budget.py` compares these counts with its budget; `tools/ruff_stats.py` groups the ruff counts per prefix.
"""

import json
import shutil
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_FILE = ROOT / "pyproject.toml"
PYRIGHT_STRICT_CONFIG = ROOT / "pyrightconfig.strict.json"
CHECK_PATHS = ("src", "test", "tools", "features")


def _tool_command(tool: str) -> list[str]:
    """Return the command that runs `tool`, preferring the installed executable."""
    executable = shutil.which(tool)
    return [executable] if executable else [sys.executable, "-m", tool]


def _run(command: list[str], max_exit_code: int) -> str:
    """Run `command` in the repository root and return its stdout, or raise when it fails."""
    # encoding is explicit because the tools emit UTF-8 while Windows decodes with the ANSI code page by default.
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", cwd=ROOT, check=False)  # noqa: S603 (command built from constants here)
    if result.returncode > max_exit_code:
        message = f"{Path(command[0]).name} failed (exit code {result.returncode}):\n{result.stderr.strip()}"
        raise RuntimeError(message)
    return result.stdout


def _parse_json(output: str, opening: str):
    """Parse the JSON document in `output`, skipping any message the tool printed before it."""
    start = output.find(opening)
    if start < 0:
        message = f"no JSON output found; the tool reported:\n{output.strip()}"
        raise RuntimeError(message)
    return json.loads(output[start:])


def run_json_array(tool: str, arguments: list[str], max_exit_code: int = 0) -> list[dict[str, Any]]:
    """Run `tool` with `arguments` and parse the JSON array it prints."""
    return _parse_json(_run([*_tool_command(tool), *arguments], max_exit_code), "[")


def count_ruff_issues(*, preview: bool = False) -> Counter[str]:
    """Count the ruff issues per rule code with every rule selected, optionally in ruff's preview mode."""
    # `--select` on the command line replaces the whole configured selection, so the deliberate ignores are repeated here.
    with PYPROJECT_FILE.open("rb") as file:
        ignored = tomllib.load(file)["tool"]["ruff"]["lint"]["ignore"]
    options = ["--ignore", ",".join(ignored)] if ignored else []
    if preview:
        options.append("--preview")
    arguments = ["check", "--select", "ALL", *options, "--output-format", "json", "--quiet", *CHECK_PATHS]
    diagnostics = run_json_array("ruff", arguments, max_exit_code=1)
    return Counter(diagnostic.get("code") or "syntax-error" for diagnostic in diagnostics)


def count_pyright_issues() -> Counter[str]:
    """Count the pyright errors and warnings per rule with strict type checking enabled."""
    # --pythonpath points pyright at the interpreter running this script, so it resolves the same dependencies.
    command = [*_tool_command("pyright"), "--project", str(PYRIGHT_STRICT_CONFIG), "--pythonpath", sys.executable, "--outputjson"]
    report = _parse_json(_run(command, max_exit_code=1), "{")
    return Counter(
        diagnostic.get("rule") or f"general-{diagnostic['severity']}"
        for diagnostic in report.get("generalDiagnostics", [])
        if diagnostic.get("severity") in {"error", "warning"}
    )

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Ruff fixes and formatting for the files a recipe changed."""

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def run_ruff_import_cleanup(paths: Sequence[Path]) -> None:
    """Remove unused imports and sort the imports of each file in place.

    Runs `ruff check --fix --select F401,I001` with the ruff settings that apply to each path. Does nothing when
    paths is empty.
    """
    if not paths:
        return
    subprocess.run(  # noqa: S603 (fixed arguments plus the caller's paths, no shell)
        [sys.executable, "-m", "ruff", "check", "--fix", "--select", "F401,I001", *(str(path) for path in paths)],
        capture_output=True,
        check=False,
    )


def run_ruff_format(paths: Sequence[Path]) -> None:
    """Format each whole file in place.

    Runs `ruff format` with the ruff settings that apply to each path. Does nothing when paths is empty.
    """
    if not paths:
        return
    subprocess.run(  # noqa: S603 (fixed arguments plus the caller's paths, no shell)
        [sys.executable, "-m", "ruff", "format", *(str(path) for path in paths)],
        capture_output=True,
        check=False,
    )

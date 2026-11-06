# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""List the files of the repository: those that git tracks or would track, and the directories that hold them.

`tools/check_layout.py` and `tools/check_references.py` check paths against these files.
"""

import shutil
import subprocess
from collections.abc import Iterable
from pathlib import Path


def list_files(root: Path) -> set[str]:
    """Return the files in `root` that git tracks or would track, or raise when git is unavailable or fails."""
    git = shutil.which("git")
    if git is None:
        message = "git was not found on PATH, so the files cannot be listed"
        raise RuntimeError(message)
    command = [git, "ls-files", "--cached", "--others", "--exclude-standard", "-z"]
    result = subprocess.run(command, capture_output=True, cwd=root, check=False)  # noqa: S603 (command built from constants here)
    if result.returncode != 0:
        message = f"git ls-files failed (exit code {result.returncode}):\n{result.stderr.decode('utf-8', 'replace').strip()}"
        raise RuntimeError(message)
    # A file deleted from the working tree stays in the index until the deletion is staged.
    return {path for path in result.stdout.decode("utf-8").split("\0") if path and (root / path).is_file()}


def with_directories(files: Iterable[str]) -> set[str]:
    """Return `files` together with every directory that holds one of them, each directory ending with `/`."""
    paths = set(files)
    for file in list(paths):
        parts = file.split("/")[:-1]
        paths.update("/".join(parts[: depth + 1]) + "/" for depth in range(len(parts)))
    return paths

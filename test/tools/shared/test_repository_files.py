# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the file listing in tools/shared/repository_files.py."""

import shutil
import subprocess
from pathlib import Path

import pytest

from tools.shared import repository_files


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_untracked_files_count_and_ignored_files_do_not(tmp_path: Path) -> None:
    """Assert the files are those git tracks or would track: a new file counts, an ignored one does not."""
    git = shutil.which("git")
    assert git is not None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    subprocess.run([git, "init", "-q"], cwd=tmp_path, check=True)  # noqa: S603 (git from PATH, fixed arguments)
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "check_a.py").write_text("")
    (tmp_path / "tools" / "ignored.py").write_text("")
    assert repository_files.list_files(tmp_path) == {".gitignore", "tools/check_a.py"}  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_every_directory_that_holds_a_file_is_added() -> None:
    """Assert each directory above a file is added once, ending with `/`."""
    paths = repository_files.with_directories({"a/b/c.py", "a/d.py", "e.py"})
    assert paths == {"a/b/c.py", "a/d.py", "e.py", "a/", "a/b/"}  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)

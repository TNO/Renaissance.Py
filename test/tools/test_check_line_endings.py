# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the line-ending guard rail in tools/check_line_endings.py.

The unit tests parse synthetic `git ls-files --eol` output; the integration tests run git in a
temporary repository, so they verify the parsing against the output git really produces.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from tools import check_line_endings


def _record(index_eol: str, attributes: str, path: str) -> str:
    """Return one NUL-terminated record in the layout of `git ls-files --eol -z`."""
    return f"i/{index_eol:<5} w/{index_eol:<5} attr/{attributes:<20}\t{path}\0"


def _violating_paths(output: str) -> list[str]:
    """Return the paths that the check reports for the `git ls-files --eol -z` output `output`."""
    return [violation.path for violation in check_line_endings.find_violations(check_line_endings.parse_ls_files_eol(output))]


def test_attributes_containing_spaces_and_paths_containing_spaces_are_parsed() -> None:
    """Assert a record is split on its TAB, so neither the attributes nor the path are cut at a space."""
    files = check_line_endings.parse_ls_files_eol(_record("lf", "text=auto eol=lf", "docs/my notes.md"))
    expected = [check_line_endings.TrackedFile(path="docs/my notes.md", index_eol="lf", attributes=("text=auto", "eol=lf"))]
    assert files == expected  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_lf_and_files_without_line_endings_are_accepted() -> None:
    """Assert LF files, files without any line ending, and binary content pass."""
    output = _record("lf", "", "a.py") + _record("none", "", "b.txt") + _record("-text", "", "c.png")
    assert _violating_paths(output) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_crlf_and_mixed_files_are_reported() -> None:
    """Assert a file stored with CRLF and a file stored with mixed line endings are both reported."""
    output = _record("mixed", "", "b.py") + _record("crlf", "", "a.py")
    assert _violating_paths(output) == ["a.py", "b.py"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_file_whose_text_conversion_is_switched_off_is_exempt() -> None:
    """Assert a file marked `-text` may keep CRLF, since that is how a CRLF fixture is committed on purpose."""
    assert _violating_paths(_record("crlf", "-text", "fixture.c")) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.fixture
def git_repository(tmp_path: Path) -> Path:
    """Return an empty git repository that does not convert line endings unless its attributes say so."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not on PATH")
    subprocess.run([git, "init", "--quiet"], cwd=tmp_path, check=True)  # noqa: S603 (command built from constants here)
    # A developer's global autocrlf would otherwise decide what these tests store.
    subprocess.run([git, "config", "core.autocrlf", "false"], cwd=tmp_path, check=True)  # noqa: S603 (command built from constants here)
    return tmp_path


def _stage(repository: Path, files: dict[str, bytes]) -> list[str]:
    """Write `files` into `repository`, stage them, and return the paths the check reports."""
    for name, content in files.items():
        (repository / name).write_bytes(content)
    subprocess.run([shutil.which("git") or "git", "add", "--all"], cwd=repository, check=True)  # noqa: S603 (command built from constants here)
    return [violation.path for violation in check_line_endings.find_violations(check_line_endings.list_tracked_files(repository))]


def test_a_staged_crlf_file_is_reported_without_gitattributes(git_repository: Path) -> None:
    """Assert the check catches CRLF that reaches the index when no `.gitattributes` normalizes it."""
    assert _stage(git_repository, {"lf.py": b"a\nb\n", "crlf.py": b"a\r\nb\r\n"}) == ["crlf.py"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_gitattributes_normalizes_crlf_before_it_reaches_the_index(git_repository: Path) -> None:
    """Assert the attribute this repository uses converts CRLF to LF, so nothing is left to report."""
    files = {".gitattributes": b"* text=auto eol=lf\n", "crlf.py": b"a\r\nb\r\n"}
    assert _stage(git_repository, files) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_fixture_marked_minus_text_keeps_crlf_and_is_exempt(git_repository: Path) -> None:
    """Assert a fixture directory marked `-text` keeps its CRLF bytes in the index and passes the check."""
    (git_repository / "crlf").mkdir()
    files = {".gitattributes": b"* text=auto eol=lf\ncrlf/** -text\n", "crlf/input.c": b"int a;\r\n"}
    assert _stage(git_repository, files) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    stored = subprocess.run(  # noqa: S603 (command built from constants here)
        [shutil.which("git") or "git", "show", ":crlf/input.c"], cwd=git_repository, capture_output=True, check=True
    ).stdout
    assert stored == b"int a;\r\n"  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_binary_files_are_exempt(git_repository: Path) -> None:
    """Assert a file marked `binary`, as the images in this repository are, is never reported."""
    files = {".gitattributes": b"*.png binary\n", "image.png": b"\x89PNG\r\n\x1a\n"}
    assert _stage(git_repository, files) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)

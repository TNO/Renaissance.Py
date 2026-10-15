# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the copyright guard rail in tools/check_copyright.py.

The `tools` directory is not on the pytest `pythonpath`, so the script is loaded from its path.
The unit tests work on bytes with a synthetic notice; the end-to-end tests run against a temporary git repository.
"""

import importlib.util
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]

NOTICE = ("Copyright (C) 2024-2026 Example", "", "Licensed as described in LICENSE.")
PYTHON_NOTICE = b"# Copyright (C) 2024-2026 Example\n#\n# Licensed as described in LICENSE.\n"
MARKDOWN_NOTICE = b"<!--\nCopyright (C) 2024-2026 Example\n\nLicensed as described in LICENSE.\n-->\n"


def _load_check_copyright() -> ModuleType:
    """Import tools/check_copyright.py as a module."""
    path = ROOT / "tools" / "check_copyright.py"
    spec = importlib.util.spec_from_file_location("check_copyright", path)
    if spec is None or spec.loader is None:
        message = f"cannot load {path}"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_copyright = _load_check_copyright()


def _apply(command: str, name: str, data: bytes) -> tuple[bytes, str | None]:
    """Apply `command` to a file called `name` with content `data`."""
    return check_copyright.handle(command, PurePosixPath(name), data, NOTICE)


ROUND_TRIP_CASES = [
    ("empty.py", b""),
    ("code.py", b'"""Docstring."""\n\nx = 1\n'),
    ("no_final_newline.py", b"x = 1"),
    ("crlf.py", b"x = 1\r\ny = 2\r\n"),
    ("cr.py", b"x = 1\ry = 2\r"),
    ("bom.py", b"\xef\xbb\xbfx = 1\n"),
    ("script.py", b"#!/usr/bin/env python\nx = 1\n"),
    ("latin1.py", b"# -*- coding: latin-1 -*-\ns = '\xe9'\n"),
    ("shebang_and_coding.py", b"#!/usr/bin/env python\n# coding: utf-8\nx = 1\n"),
    ("only_shebang.py", b"#!/usr/bin/env python\n"),
    ("page.md", b"# Title\n\nText.\n"),
    ("front_matter.md", b"---\ntitle: Page\n---\n# Title\n"),
    ("dutch.feature", b"# language: nl\nFunctionaliteit: X\n"),
    ("settings.toml", b"[tool]\nkey = 1\n"),
    ("workflow.yml", b"name: CI\n"),
    (".gitignore", b"*.pyc\n"),
]


@pytest.mark.parametrize(("name", "data"), ROUND_TRIP_CASES)
def test_insert_then_remove_restores_the_original_bytes(name: str, data: bytes) -> None:
    """Insert and remove are each other's inverse, are idempotent, and leave a file that passes the check."""
    inserted, violation = _apply("insert", name, data)
    assert violation is None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert inserted != data  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert _apply("check", name, inserted) == (inserted, None)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert _apply("insert", name, inserted) == (inserted, None)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert _apply("remove", name, inserted) == (data, None)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert _apply("remove", name, data) == (data, None)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.mark.parametrize(
    ("name", "data", "expected"),
    [
        ("empty.py", b"", PYTHON_NOTICE),
        ("code.py", b"x = 1\n", PYTHON_NOTICE + b"\nx = 1\n"),
        ("no_final_newline.py", b"x = 1", PYTHON_NOTICE + b"\nx = 1"),
        ("crlf.py", b"x = 1\r\n", PYTHON_NOTICE.replace(b"\n", b"\r\n") + b"\r\nx = 1\r\n"),
        ("bom.py", b"\xef\xbb\xbfx = 1\n", b"\xef\xbb\xbf" + PYTHON_NOTICE + b"\nx = 1\n"),
        ("script.py", b"#!/bin/python\n# coding: latin-1\nx\n", b"#!/bin/python\n# coding: latin-1\n" + PYTHON_NOTICE + b"\nx\n"),
        ("late_coding.py", b"x = 1\n# coding: latin-1\n", PYTHON_NOTICE + b"\nx = 1\n# coding: latin-1\n"),
        ("page.md", b"# Title\n", MARKDOWN_NOTICE + b"\n# Title\n"),
        ("front_matter.md", b"---\na: 1\n---\n# T\n", b"---\na: 1\n---\n" + MARKDOWN_NOTICE + b"\n# T\n"),
        ("dutch.feature", b"# language: nl\nX\n", b"# language: nl\n" + PYTHON_NOTICE + b"\nX\n"),
    ],
)
def test_insert_places_the_notice_after_the_lines_that_must_stay_first(name: str, data: bytes, expected: bytes) -> None:
    """The notice follows a BOM, shebang, encoding declaration, language line or front matter, and is followed by one blank line."""
    assert _apply("insert", name, data) == (expected, None)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.mark.parametrize(
    ("name", "data", "reason"),
    [
        ("code.py", b"x = 1\n", "notice missing"),
        ("outdated.py", b"# Copyright (C) 2020 Example\n\nx = 1\n", "modified or outdated"),
        ("moved.py", b"x = 1\n" + PYTHON_NOTICE, "wrong position"),
        ("unspaced.py", PYTHON_NOTICE.replace(b"# ", b"#") + b"\nx = 1\n", "wrong comment style or layout"),
        ("styled.md", b"<!-- Copyright (C) 2024-2026 Example -->\n<!-- Licensed as described in LICENSE. -->\n", "wrong comment style"),
        ("cramped.py", PYTHON_NOTICE + b"x = 1\n", "not followed by a blank line"),
        ("unterminated.py", PYTHON_NOTICE.removesuffix(b"\n"), "not followed by a line ending"),
        ("above_shebang.py", PYTHON_NOTICE + b"\n#!/usr/bin/env python\n", "above a shebang or encoding declaration"),
        ("mixed.py", b"x = 1\ny = 2\r\n", "mixed line endings"),
        ("utf16.py", b"\xff\xfex\x00", "UTF-16 and UTF-32"),
        ("bad_utf8.py", b"s = '\xe9'\n", "not valid utf-8"),
        ("unknown.py", b"# coding: no-such-codec\n", "unknown encoding"),
        ("wide.py", b"# coding: utf-16\n", "not ASCII compatible"),
        ("contradiction.py", b"\xef\xbb\xbf# coding: latin-1\n", "byte order mark contradicts"),
        ("only_shebang.py", b"#!/usr/bin/env python", "without a line ending"),
        ("data.csv", b"a,b\n", "unmapped file type"),
    ],
)
def test_check_reports_the_reason(name: str, data: bytes, reason: str) -> None:
    """Each kind of violation has its own reason; unless the notice is simply missing, neither insert nor remove touches the file."""
    commands = ("check",) if reason == "notice missing" else ("check", "insert", "remove")
    for command in commands:
        new_data, violation = _apply(command, name, data)
        assert new_data == data  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
        assert violation is not None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
        assert reason in violation  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_notice_that_cannot_be_encoded_is_reported() -> None:
    """A file whose declared encoding cannot represent the notice is left alone."""
    data = b"# coding: ascii\nx = 1\n"
    new_data, violation = check_copyright.handle("insert", PurePosixPath("a.py"), data, ("Copyright (C) 2024 \u00c9xample",))
    assert new_data == data  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert violation == "the notice cannot be encoded in ascii"  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_notice_is_encoded_in_the_declared_encoding() -> None:
    """A non-ASCII notice is written in the encoding the file declares."""
    data = b"# coding: latin-1\nx = 1\n"
    inserted, violation = check_copyright.handle("insert", PurePosixPath("a.py"), data, ("Copyright (C) 2024 \u00c9xample",))
    assert violation is None  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert inserted == b"# coding: latin-1\n# Copyright (C) 2024 \xc9xample\n\nx = 1\n"  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_copyright_text_below_the_header_is_not_a_modified_notice() -> None:
    """Only the comments that open the file count as its header."""
    data = b'"""Docstring."""\n\n# Copyright (C) 2016 Someone Else\n'
    assert _apply("check", "a.py", data) == (data, "notice missing")  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "non-empty line"),
        ("\nCopyright (C) 2024 Example\n", "non-empty line"),
        ("\ufeffCopyright (C) 2024 Example\n", "byte order mark"),
        ("Copyright (C) 2024 Example \n", "trailing whitespace"),
    ],
)
def test_an_invalid_notice_file_is_rejected(tmp_path: Path, content: str, message: str) -> None:
    """The notice must start with a non-empty line and have no trailing whitespace."""
    path = tmp_path / "COPYRIGHT.txt"
    path.write_bytes(content.encode("utf-8"))
    with pytest.raises(ValueError, match=message):
        check_copyright.load_notice(path)


def test_the_notice_drops_trailing_empty_lines(tmp_path: Path) -> None:
    """Trailing empty lines of the notice file are not part of the notice."""
    path = tmp_path / "COPYRIGHT.txt"
    path.write_bytes(b"Copyright (C) 2024 Example\r\n\r\nLicensed.\r\n\r\n")
    assert check_copyright.load_notice(path) == ("Copyright (C) 2024 Example", "", "Licensed.")  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_notice_that_would_end_a_block_comment_is_rejected() -> None:
    """The closing marker of a block comment cannot occur in the notice."""
    with pytest.raises(ValueError, match="-->"):
        check_copyright.render(("Copyright (C) 2024 Example -->",), check_copyright.HTML)


def test_the_repository_configures_the_test_inputs() -> None:
    """The test inputs are shared with Ruff, through its extend-exclude list in pyproject.toml."""
    test_inputs = check_copyright.load_test_inputs(ROOT / "pyproject.toml")
    assert "features/targets" in test_inputs  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.mark.parametrize(
    ("path", "pattern", "expected"),
    [
        ("inputs/sample.py", "inputs", True),
        ("inputs/deep/sample.py", "inputs", True),
        ("src/inputs/sample.py", "inputs", True),
        ("inputs.py", "inputs", False),
        ("src/inputs/sample.py", "src/inputs", True),
        ("other/src/inputs/sample.py", "src/inputs", False),
        ("src/inputs/sample.py", "src/*/sample.py", True),
        ("src/sample.py", "*.py", True),
    ],
)
def test_test_inputs_match_like_ruff_exclusions(path: str, pattern: str, expected: bool) -> None:  # noqa: FBT001 (pytest parameter)
    """A pattern without a slash matches any path component; one with a slash matches from the root; both cover directories."""
    assert check_copyright.is_test_input(PurePosixPath(path), pattern) is expected  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def _git(repository: Path, *arguments: str) -> None:
    """Run git with `arguments` in `repository`."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not available")
    subprocess.run([git, *arguments], cwd=repository, check=True, capture_output=True)  # noqa: S603 (git with arguments built here)


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return a git repository with a notice, a test input, an excluded file and a file without the notice."""
    (tmp_path / "COPYRIGHT.txt").write_bytes("\n".join(NOTICE).encode("utf-8") + b"\n")
    (tmp_path / "pyproject.toml").write_bytes(b'[tool.ruff]\nextend-exclude = ["inputs"]\n')
    (tmp_path / "inputs").mkdir()
    (tmp_path / "inputs" / "sample.py").write_bytes(b"x = 1\n")
    (tmp_path / "data.json").write_bytes(b"{}\n")
    (tmp_path / "module.py").write_bytes(b"x = 1\n")
    _git(tmp_path, "init", "--quiet")
    _git(tmp_path, "add", "--all")
    monkeypatch.setattr(check_copyright, "ROOT", tmp_path)
    monkeypatch.setattr(check_copyright, "NOTICE_FILE", tmp_path / "COPYRIGHT.txt")
    monkeypatch.setattr(check_copyright, "PYPROJECT_FILE", tmp_path / "pyproject.toml")
    monkeypatch.setattr(check_copyright, "EXCLUDED", {"**/*.json": "no comments", "COPYRIGHT.txt": "the notice itself"})
    return tmp_path


def test_main_inserts_checks_and_removes(repository: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The commands work on the tracked files only, and skip excluded files and test inputs."""
    assert check_copyright.main(["check"]) == check_copyright.EXIT_VIOLATIONS  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert "module.py: notice missing" in capsys.readouterr().out  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert check_copyright.main(["insert"]) == check_copyright.EXIT_OK  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert (repository / "module.py").read_bytes() == PYTHON_NOTICE + b"\nx = 1\n"  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert (repository / "inputs" / "sample.py").read_bytes() == b"x = 1\n"  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert (repository / "pyproject.toml").read_bytes().startswith(PYTHON_NOTICE)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert check_copyright.main(["check"]) == check_copyright.EXIT_OK  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert check_copyright.main(["remove"]) == check_copyright.EXIT_OK  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert (repository / "module.py").read_bytes() == b"x = 1\n"  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_main_limits_the_run_to_the_given_paths(repository: Path) -> None:
    """With paths, only those tracked files are processed."""
    assert check_copyright.main(["insert", str(repository / "module.py")]) == check_copyright.EXIT_OK  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert (repository / "module.py").read_bytes().startswith(PYTHON_NOTICE)  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert (repository / "pyproject.toml").read_bytes().startswith(b"[tool.ruff]")  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_main_reports_an_untracked_path_as_a_tool_failure(repository: Path) -> None:
    """A path that git does not track is a usage error."""
    (repository / "untracked.py").write_bytes(b"x = 1\n")
    assert check_copyright.main(["check", str(repository / "untracked.py")]) == check_copyright.EXIT_TOOL_FAILURE  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.mark.usefixtures("repository")
def test_main_reports_a_stale_exclusion(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """An exclusion pattern that matches no tracked file fails the check."""
    monkeypatch.setattr(check_copyright, "EXCLUDED", {**check_copyright.EXCLUDED, "**/*.png": "binary image"})
    assert check_copyright.main(["insert"]) == check_copyright.EXIT_VIOLATIONS  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert "**/*.png: exclusion pattern matches no tracked file" in capsys.readouterr().out  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_main_fails_on_an_invalid_notice(repository: Path) -> None:
    """A notice file that cannot be used stops the run before any file is touched."""
    (repository / "COPYRIGHT.txt").write_bytes(b"")
    assert check_copyright.main(["insert"]) == check_copyright.EXIT_TOOL_FAILURE  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert (repository / "module.py").read_bytes() == b"x = 1\n"  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)

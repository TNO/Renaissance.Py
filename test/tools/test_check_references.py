# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the reference guard rail in tools/check_references.py.

The unit tests check synthetic files; one integration test checks the repository itself.
"""

import shutil
from collections.abc import Mapping

import pytest
from tools.shared.repository_files import with_directories

from tools import check_references

FILES = {"docs/index.md", "src/a.py", "test/unit/test_a.py"}


def _violations(contents: Mapping[str, str], config: Mapping[str, object] | None = None) -> list[str]:
    """Return the violations, as reported, of a repository holding `FILES` and the files of `contents`."""
    files = FILES | set(contents)
    parsed = check_references.parse_config(config or {})
    read = {file: content for file, content in contents.items() if check_references.is_read(file, parsed.exclude)}
    references = check_references.find_references(read, {file.split("/", 1)[0] for file in files if "/" in file})
    violations = check_references.check(references, with_directories(files), parsed)
    return [violation.describe() for violation in violations]


def test_a_missing_path_is_reported_and_existing_paths_pass() -> None:
    """Assert a missing path is reported with its file and line, and that files and directories, with or without `/`, pass."""
    contents = {"docs/page.md": "See `src/a.py`, `src/` and `test/unit`.\nThen `src/b.py`.\n"}
    assert _violations(contents) == ["docs/page.md:2: names src/b.py, which does not exist"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_markdown_link_targets_are_skipped_and_link_texts_are_read() -> None:
    """Assert the target of an inline link and of a link definition are left to mkdocs, while the link text is checked."""
    contents = {"docs/page.md": "[Gone](src/gone.md)\n[ref]: src/gone.py\n[`src/b.py`](a.md)\n"}
    assert _violations(contents) == ["docs/page.md:3: names src/b.py, which does not exist"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_only_the_comments_and_docstrings_of_python_files_are_read() -> None:
    """Assert a path in a comment or a docstring is checked, and one in a string literal is not."""
    content = '"""See src/b.py."""\n\nPATH = "src/c.py"  # see src/d.py\n\n\ndef f() -> None:\n    """See src/e.py."""\n'
    assert _violations({"src/m.py": content}) == [  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
        "src/m.py:1: names src/b.py, which does not exist",
        "src/m.py:3: names src/d.py, which does not exist",
        "src/m.py:7: names src/e.py, which does not exist",
    ]


def test_patterns_are_skipped_and_trailing_punctuation_is_not_part_of_a_path() -> None:
    """Assert names with a placeholder, a wildcard or an ellipsis are no paths, and that a sentence may end after a path."""
    contents = {"features/a.feature": "Given test/{path}/ and test/<name>.py and src/*.py and src/.../a.py\nThen src/a.py.\n"}
    assert _violations(contents) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_examples_are_skipped() -> None:
    """Assert a path with `example` as one of its words is an example, and that `examples` is not that word."""
    contents = {"docs/page.md": "`tools/example.py`, `src/example_package/a.py`, `docs/check-example.md`, `test/examples/a.py`\n"}
    assert _violations(contents) == ["docs/page.md:1: names test/examples/a.py, which does not exist"]  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_excluded_files_are_not_read() -> None:
    """Assert a file named in `exclude`, or below a directory named in it, is not read."""
    contents = {"docs/adr/one.md": "`src/gone.py`", "docs/plan.md": "`src/gone.py`"}
    assert _violations(contents, {"exclude": ["docs/adr/", "docs/plan.md"]}) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
    assert not check_references.is_read("docs/adr/one.md", ["docs/adr/"])  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


@pytest.mark.parametrize(
    ("file", "read"),
    [("docs/a.md", True), ("README.md", False), ("tools/a.py", True), ("other/a.py", False), ("features/a.feature", True)],
)
def test_the_kind_and_directory_of_a_file_decide_whether_it_is_read(file: str, *, read: bool) -> None:
    """Assert Markdown is read in `docs/` only, Python in the source directories only, and feature files everywhere."""
    assert check_references.is_read(file, []) == read  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_a_listed_missing_path_passes() -> None:
    """Assert a missing path in `known_issues` or `stale` is accepted."""
    contents = {"docs/page.md": "`src/planned.py` and `src/issue.py`\n"}
    assert _violations(contents, {"known_issues": ["src/issue.py"], "stale": ["src/planned.py"]}) == []  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)


def test_entries_that_no_longer_apply_are_reported() -> None:
    """Assert listed paths that exist or are named nowhere, and excluded paths that do not exist, fail, so the lists only shrink."""
    config = {"exclude": ["docs/gone.md"], "known_issues": ["src/a.py"], "stale": ["src/unnamed.py"]}
    assert _violations({}, config) == [  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)
        "src/a.py: is listed in `known_issues`, but exists: remove it",
        "src/unnamed.py: is listed in `stale`, but is named nowhere: remove it",
        "docs/gone.md: is listed in `exclude`, but does not exist: remove it",
    ]


@pytest.mark.parametrize(
    ("config", "message"),
    [
        ({"missing": []}, "unknown key"),
        ({"stale": "src/a.py"}, "list of strings"),
        ({"stale": ["src/a.py", "src/a.py"]}, "twice"),
        ({"known_issues": ["src/a.py"], "stale": ["src/a.py"]}, "both list"),
    ],
)
def test_an_invalid_configuration_is_rejected(config: Mapping[str, object], message: str) -> None:
    """Assert a configuration that is not valid raises `ConfigError`."""
    with pytest.raises(check_references.ConfigError, match=message):
        check_references.parse_config(config)


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_the_repository_names_existing_paths_only() -> None:
    """Assert the repository itself passes its own `[tool.check_references]`."""
    assert check_references.main([]) == check_references.EXIT_OK  # noqa: S101 (pytest assertion; new tests must not raise the S101 budget)

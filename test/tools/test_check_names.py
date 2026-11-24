# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the name guard rail in tools/check_names.py.

The unit tests check synthetic names and file lists; one integration test checks the repository itself.
"""

import shutil

import pytest
from hamcrest import all_of, assert_that, contains_string, equal_to, is_, none, not_none

from tools import check_names


@pytest.mark.parametrize(
    "name",
    [
        "check_names.py",
        "__init__.py",
        "_private.py",
        "README.md",
        "LICENSE",
        ".github",
        ".gitignore",
        "test_x.py",
        "test_x___parsing_errors.py",
        "match_finder___usage.md",
        "model",
    ],
)
def test_a_well_formed_name_passes(name: str) -> None:
    """Assert names with single `_` separators, triple ones in test and page names, outer underscores and a hidden `.` pass."""
    assert_that(check_names.check_name(name), is_(none()))


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("check-names.py", "is not an optional `.`"),
        ("check names.py", "is not an optional `.`"),
        ("check,names.py", "is not an optional `.`"),
        ("naïve.py", "is not an optional `.`"),
        ("pyrightconfig.strict.json", "is not an optional `.`"),
        ("..gitignore", "is not an optional `.`"),
        ("README.", "is not an optional `.`"),
        ("check__names.py", "by `__`"),
        ("test_x____parsing.py", "by `____`"),
        ("node___parsing.py", "only a name that starts with `test_` or ends with `.md`"),
        ("tests___x", "only a name that starts with `test_` or ends with `.md`"),
    ],
)
def test_a_malformed_name_is_reported(name: str, message: str) -> None:
    """Assert other characters, a second `.`, double underscores and triple underscores outside test and page names are reported."""
    assert_that(check_names.check_name(name), all_of(not_none(), contains_string(message)))


def test_a_directory_is_reported_once() -> None:
    """Assert a malformed directory name is reported once, not for every file it holds."""
    violations = check_names.find_violations({"docs/bad-dir/a.md", "docs/bad-dir/b.md", "docs/good.md"})
    assert_that([violation.path for violation in violations], equal_to(["docs/bad-dir/"]))


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_the_repository_names_pass() -> None:
    """Assert the repository itself passes its own naming rule."""
    assert_that(check_names.main([]), equal_to(check_names.EXIT_OK))

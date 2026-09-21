"""Tests for the Clang-based LST adapter."""

from pathlib import Path

import pytest
from hamcrest import assert_that, greater_than, has_length, is_

import targets
from renaissance.integrations.clang.clang_adapter import ClangAdapter
from renaissance.integrations.tree_sitter.lst import LST
from renaissance.utils.ast_utils import traverse


class TestClangAdapter:
    """AI: Tests for the Clang-based LST adapter."""

    def test_parse_cpp_file(self):
        """AI: Verify parsing a C++ example file produces a traversable LST."""
        adapter = ClangAdapter()
        lst = adapter.parse(Path(targets.__file__).parent / "cpp_example.cpp")
        assert_that(lst, is_(LST))
        assert_that(list(traverse(lst.root)), has_length(greater_than(0)))


if __name__ == "__main__":
    pytest.main()

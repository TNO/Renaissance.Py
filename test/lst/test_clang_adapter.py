import pytest
from hamcrest import *
from pathlib import Path

import targets
from renaissance.impl.clang.clang_adapter import ClangAdapter
from renaissance.impl.tree_sitter.lst import LST
from renaissance.utils.ast_utils import traverse


class TestClangAdapter:
    def test_parse_cpp_file(self):
        adapter = ClangAdapter()
        lst = adapter.parse(Path(targets.__file__).parent / "cpp_example.cpp")
        assert_that(lst, is_(LST))
        assert_that(list(traverse(lst.root)), has_length(greater_than(0)))


if __name__ == "__main__":
    pytest.main()

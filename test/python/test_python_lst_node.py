import pytest
import tree_sitter_python
from hamcrest import assert_that, is_

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.tree_sitter.lst import LSTNode


class TestPythonCstNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(LSTNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_stmt_kind(self):
        src = self.factory.create_from_text("x =1")
        target = self.factory.create_from_text("x   =  1")
        assert_that(src, is_(target))

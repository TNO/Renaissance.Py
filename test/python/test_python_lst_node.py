import hypothesmith
import libcst
import pytest
from hamcrest import assert_that, is_, instance_of
from hypothesis import given, settings, HealthCheck

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.tree_sitter.lst import LSTNode
from renaissance.impl.types import Statement
from utils_for_tests import reject_unsupported_code


class TestPythonLstNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(LSTNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_stmt_kind(self):
        src = self.factory.create_from_text("x =1")
        target = self.factory.create_from_text("x   =  1")
        assert_that(src, is_(target))

    @given(code=hypothesmith.from_node(libcst.BaseStatement))
    @settings(max_examples=500)
    def test_from_cst_returns_statement(self, code):
        reject_unsupported_code(code)
        factory = PythonFactory(LSTNode)
        node = factory.create_from_text(code)
        print(f"testing {code=} with LSTNode")
        assert_that(node.children[0].ast_type(), instance_of(Statement), f"{code=}")



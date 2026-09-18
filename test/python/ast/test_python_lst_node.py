import hypothesmith
import libcst
import pytest
from hamcrest import assert_that, is_
from hypothesis import HealthCheck, given, settings

from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.tree_sitter.lst import LSTNode
from renaissance.syntax_tree.semantic_kind import SemanticKind
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

    @pytest.mark.hypothesisslow
    @given(code=hypothesmith.from_node(libcst.BaseStatement))
    @settings(max_examples=500, suppress_health_check=list(HealthCheck))
    def test_from_cst_returns_statement(self, code):
        reject_unsupported_code(code)
        factory = PythonFactory(LSTNode)
        node = factory.create_from_text(code)
        print(f"testing {code=} with LSTNode")
        assert_that(node.children[0].semantic_kind is not SemanticKind.NODE, is_(True), f"{code=}")

    @pytest.mark.xfail(
        reason="LSTNode.__hash__ is derived from self.children, which add_child() mutates after "
        "construction - mutating a node already stored in a set corrupts its hash bucket, so "
        "membership checks silently fail even though the object is still the set's only member.",
        strict=True,
    )
    def test_hash_stays_stable_after_add_child(self):
        parent = LSTNode("block", {}, "block text")
        child = LSTNode("stmt", {"name": "a"}, "a;")
        nodes = {parent}
        parent.add_child(child)
        assert_that(parent in nodes, is_(True))

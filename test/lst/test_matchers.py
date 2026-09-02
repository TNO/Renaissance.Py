import pytest
import tree_sitter_cpp as tscpp
from hamcrest import assert_that, has_length

from renaissance.impl.tree_sitter.adapter import TreeSitterAdapter
from renaissance.impl.tree_sitter.lst import LSTNode
from renaissance.impl.types import Call
from renaissance.syntax_tree.ast_finder import find_ast_type
from renaissance.syntax_tree.match_finder import is_match
from renaissance.utils.ast_utils import traverse


class TestMatchers:
    @pytest.fixture(autouse=True)
    def setUp(self):
        adapter = TreeSitterAdapter(tscpp)
        self.if_node = self.make_pattern("if (x > 0) print(x);", adapter)
        self.for_node = self.make_pattern("for (i in range(10)) print(i);", adapter)
        self.while_node = self.make_pattern("while (x < 10) x += 1;", adapter)
        self.try_node = self.make_pattern(
            "try { risky_operation(); } catch (Exception e) { handle_error(e); }",
            adapter,
        )
        self.class_node = self.make_pattern("class MyClass { method(self) { pass; } }", adapter)

    def test_if_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern("if ($x > 0) print($x);", adapter)

        assert_that(is_match(self.if_node, pattern))

    def test_for_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern("for ($i in range(10)) print($i);", adapter)
        assert_that(is_match(self.for_node, pattern))

    def test_while_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern("while ($x < 10) $x += 1;", adapter)
        assert_that(is_match(self.while_node, pattern))

    def test_try_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern(
            "try { risky_operation(); } catch (Exception $e) { handle_error($e); }",
            adapter,
        )
        assert_that(is_match(self.try_node, pattern))

    def test_class_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern("class MyClass { method(self) { pass; } }", adapter)
        assert_that(is_match(self.class_node, pattern))

    def test_node_type_match(self):
        matches = [node for node in traverse(self.if_node) if node.ast_type == Call]
        assert_that(matches, has_length(1))

    def test_node_type_match_exact_type(self):
        matches = find_ast_type(self.if_node, Call)
        assert_that(matches, has_length(1))

    def make_pattern(self, code: str, adapter: any) -> LSTNode:
        tree = adapter.parse_code(code)
        root = adapter.to_lst(code, tree)
        return root.root


if __name__ == "__main__":
    pytest.main()

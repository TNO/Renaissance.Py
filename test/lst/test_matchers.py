import pytest
from hamcrest import *
import tree_sitter_cpp as tscpp
from hamcrest import assert_that, has_length

from renaissance.impl.tree_sitter_adapter.tree_sitter_adapter import TreeSitterAdapter
from renaissance.lst.lst import LSTNode

from renaissance.syntax_tree import ASTFinder
from renaissance.syntax_tree.match_finder import is_match


def make_pattern(code: str, adapter: any) -> LSTNode:
    tree = adapter.parse_code(code)
    root = adapter.to_lst(code, tree)
    return root.root


class TestMatchers:

    @pytest.fixture(autouse=True)
    def setUp(self):
        adapter = TreeSitterAdapter(tscpp)
        self.if_node = make_pattern("if (x > 0) print(x);", adapter)
        self.for_node = make_pattern("for (i in range(10)) print(i);", adapter)
        self.while_node = make_pattern("while (x < 10) x += 1;", adapter)
        self.try_node = make_pattern(
            "try { risky_operation(); } catch (Exception e) { handle_error(e); }",
            adapter,
        )
        self.class_node = make_pattern("class MyClass { method(self) { pass; } }", adapter)

    def test_if_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("if ($x > 0) print($x);", adapter)

        assert_that(is_match(self.if_node, pattern))

    def test_for_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("for ($i in range(10)) print($i);", adapter)
        assert_that(is_match(self.for_node, pattern))

    def test_while_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("while ($x < 10) $x += 1;", adapter)
        assert_that(is_match(self.while_node, pattern))

    def test_try_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern(
            "try { risky_operation(); } catch (Exception $e) { handle_error($e); }",
            adapter,
        )
        assert_that(is_match(self.try_node, pattern))

    def test_class_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("class MyClass { method(self) { pass; } }", adapter)
        assert_that(is_match(self.class_node, pattern))

    def test_node_type_match(self):
        matches = ASTFinder.find_kind(self.if_node, "call_?expression").to_list()
        assert_that(matches, has_length(1))

    @pytest.mark.skip("I expect 'call_expression' to work, or a defined way to get kind")
    def test_node_type_match_exact_type(self):
        matches = ASTFinder.find_kind(self.if_node, "call_expression").to_list()
        assert_that(matches, has_length(1))


if __name__ == "__main__":
    pytest.main()

"""Tests for matching tree-sitter LST nodes by semantic kind."""

import pytest
import tree_sitter_cpp as tscpp
from hamcrest import assert_that, has_length

from renaissance.integrations.tree_sitter.adapter import TreeSitterAdapter
from renaissance.integrations.tree_sitter.lst import LSTNode
from renaissance.syntax_tree.ast_finder import find_semantic_kind
from renaissance.syntax_tree.match_finder import is_match
from renaissance.syntax_tree.semantic_kind import SemanticKind
from renaissance.utils.ast_utils import traverse


class TestMatchers:
    """AI: Tests for matching tree-sitter LST nodes by semantic kind."""

    @pytest.fixture(autouse=True)
    def setUp(self):
        """AI: Build if/for/while/try/class pattern nodes shared by the matcher tests."""
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
        """AI: Verify an if-statement node matches an equivalent placeholder if-pattern."""
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern("if ($x > 0) print($x);", adapter)

        assert_that(is_match(self.if_node, pattern))

    def test_for_pattern_match(self):
        """AI: Verify a for-statement node matches an equivalent placeholder for-pattern."""
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern("for ($i in range(10)) print($i);", adapter)
        assert_that(is_match(self.for_node, pattern))

    def test_while_pattern_match(self):
        """AI: Verify a while-statement node matches an equivalent placeholder while-pattern."""
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern("while ($x < 10) $x += 1;", adapter)
        assert_that(is_match(self.while_node, pattern))

    def test_try_pattern_match(self):
        """AI: Verify a try/catch statement node matches an equivalent placeholder try-pattern."""
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern(
            "try { risky_operation(); } catch (Exception $e) { handle_error($e); }",
            adapter,
        )
        assert_that(is_match(self.try_node, pattern))

    def test_class_pattern_match(self):
        """AI: Verify a class-statement node matches an identical class-pattern."""
        adapter = TreeSitterAdapter(tscpp)
        pattern = self.make_pattern("class MyClass { method(self) { pass; } }", adapter)
        assert_that(is_match(self.class_node, pattern))

    def test_node_type_match(self):
        """AI: Verify traversing the if-node finds exactly one CALL-kind descendant."""
        matches = [node for node in traverse(self.if_node) if node.semantic_kind is SemanticKind.CALL]
        assert_that(matches, has_length(1))

    def test_node_type_match_exact_type(self):
        """AI: Verify find_semantic_kind finds exactly one CALL-kind descendant of the if-node."""
        matches = find_semantic_kind(self.if_node, SemanticKind.CALL)
        assert_that(matches, has_length(1))

    def make_pattern(self, code: str, adapter: any) -> LSTNode:
        """AI: Parse code with the given adapter and return the resulting LST's root node."""
        tree = adapter.parse_code(code)
        root = adapter.to_lst(code, tree)
        return root.root


if __name__ == "__main__":
    pytest.main()

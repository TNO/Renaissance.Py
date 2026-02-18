import unittest
import tree_sitter_cpp as tscpp

from impl.tree_sitter_adapter.tree_sitter_adapter import TreeSitterAdapter
from lst.lst import LSTNode
from lst_matchers.node_type_matcher import NodeTypeMatcher
from syntax_tree.match_finder import is_match


# from matchers.pattern_matcher import MatchResult


def make_pattern(code: str, adapter: any) -> LSTNode:
    tree = adapter.parse_code(code)
    root = adapter.to_lst(code, tree)
    return root.root


class TestMatchers(unittest.TestCase):
    def setUp(self):
        adapter = TreeSitterAdapter(tscpp)
        self.if_node = make_pattern("if (x > 0) print(x);", adapter)
        self.for_node = make_pattern("for (i in range(10)) print(i);", adapter)
        self.while_node = make_pattern("while (x < 10) x += 1;", adapter)
        self.try_node = make_pattern(
            "try { risky_operation(); } catch (Exception e) { handle_error(e); }",
            adapter,
        )
        self.class_node = make_pattern(
            "class MyClass { method(self) { pass; } }", adapter
        )

    def test_if_pattern_match(self):

        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("if ($x > 0) print($x);", adapter)

        self.assertTrue(is_match(self.if_node, pattern))

    def test_for_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("for ($i in range(10)) print($i);", adapter)
        self.assertTrue(is_match(self.for_node, pattern))

    def test_while_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("while ($x < 10) $x += 1;", adapter)
        self.assertTrue(is_match(self.while_node, pattern))

    def test_try_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern(
            "try { risky_operation(); } catch (Exception $e) { handle_error($e); }",
            adapter,
        )
        self.assertTrue(is_match(self.try_node, pattern))

    def test_class_pattern_match(self):
        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("class MyClass { method(self) { pass; } }", adapter)
        self.assertTrue(is_match(self.class_node, pattern))

    def test_node_type_match(self):
        matcher = NodeTypeMatcher("call_expression")
        matches = matcher.match(self.if_node)
        self.assertEqual(len(matches), 1)


if __name__ == "__main__":
    unittest.main()

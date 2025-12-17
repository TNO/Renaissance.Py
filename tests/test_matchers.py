import unittest
import tree_sitter_cpp as tscpp
from adapters.tree_sitter_adapter import TreeSitterAdapter
from lst.lst import LSTNode
from matchers.pattern_matcher import StructuralPatternMatcher
from matchers.node_type_matcher import NodeTypeMatcher

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

    def test_structural_pattern_match(self):

        adapter = TreeSitterAdapter(tscpp)
        pattern = make_pattern("if ($x > 0) print($x);", adapter)

        matcher = StructuralPatternMatcher(pattern)
        matches = matcher.match(self.if_node)
        self.assertEqual(len(matches), 1)

        pattern = make_pattern("for ($i in range(10)) print($i);", adapter)
        matcher = StructuralPatternMatcher(pattern)
        matches = matcher.match(self.for_node)
        self.assertEqual(len(matches), 1)
        pattern = make_pattern("while ($x < 10) $x += 1;", adapter)
        matcher = StructuralPatternMatcher(pattern)
        matches = matcher.match(self.while_node)
        self.assertEqual(len(matches), 1)
        pattern = make_pattern(
            "try { risky_operation(); } catch (Exception $e) { handle_error($e); }",
            adapter,
        )
        matcher = StructuralPatternMatcher(pattern)
        matches = matcher.match(self.try_node)
        self.assertEqual(len(matches), 1)
        pattern = make_pattern("class MyClass { method(self) { pass; } }", adapter)
        matcher = StructuralPatternMatcher(pattern)
        matches = matcher.match(self.class_node)
        self.assertEqual(len(matches), 1)

    def test_node_type_match(self):
        matcher = NodeTypeMatcher("call_expression")
        matches = matcher.match(self.if_node)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].bindings["match"][0].node_type, "call_expression")


if __name__ == "__main__":
    unittest.main()

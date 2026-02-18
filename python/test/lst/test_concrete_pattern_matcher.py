import unittest

from parameterized import parameterized

from extractors.extractor import PatternMatcherInterfaceExtended, Extractor
from impl.tree_sitter_adapter.tree_sitter_adapter import TreeSitterAdapter
from impl.tree_sitter_adapter.ts_pattern_factory import TsPatternFactory
from lst.lst import LSTNode
import tree_sitter_python as tspython

from syntax_tree.match_finder import is_match, is_match_tree


class TestConcretePatternMatcher(unittest.TestCase):

    @parameterized.expand([
        ("def foo(): pass", "def foo(): pass"),
        ("if x:  print(x)", "if x:  $body"),
        ("for i in range(10): print(i)", "for $i in $iter: $body"),
        ("while True: pass", "while $cond: $body"),
        ("try: pass\nexcept Exception: pass", "try: $b\nexcept Exception: $b"),
        ("class A: pass", "class $C: $body"),
        ("with open('x') as f: pass","with $ctx as $var: $body"),
        ("assert x", "assert $cond"),
        ("return x", "return $value"),
        ("lambda x: x", "lambda $arg: $body"),
        ("a = b", "$lhs = $rhs"),
        ("a += b", "$lhs += $rhs"),
        ("x and y", "$left and $right"),
        ("not x", "not $expr"),
        ("x if y else z", "$t if $cond else $f"),
        ("f(x)", "$func($arg)"),
        ("[x for x in y]", "[$x for $x in $y]"),
        ("x in y", "$x in $y"),
        ("import os", "import $mod"),
    ])
    def test_python_patterns(self, code, pattern):
        self.adapter = TreeSitterAdapter(tspython)
        self.interface = TsPatternFactory(self.adapter)
        extractor = Extractor(self.interface)
        extractor.add_rule(pattern)
        matches = extractor.run(code)

        self.assertTrue(len(matches) >= 1, f"Pattern failed: {pattern}")



def test_is_match_python_patterns():
    adapter = TreeSitterAdapter(tspython)
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("try: pass\nexcept Exception: pass")
    p = interface.create_statement("try: $b\nexcept Exception: $b")
    assert is_match(c.children[0], p.children[0], {})
    assert is_match(c.children[1], p.children[1], {})
    assert is_match(c.children[2], p.children[2], {})
    assert is_match(c.children[3], p.children[3], {})


def test_is_match_python_patterns_tree():
    adapter = TreeSitterAdapter(tspython)
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("try: pass\nexcept Exception: pass")
    p = interface.create_statement("try: $b\nexcept Exception: $b")
    assert is_match_tree(c.children, p.children, {})

def test_is_match_python_patterns_1():
    adapter = TreeSitterAdapter(tspython)
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("if x:  print(x)")
    p = interface.create_statement("if x:  $body")
    assert is_match(c, p, {})


# def test_python_patterns_tree_1(self):
#     adapter = TreeSitterAdapter(tspython)
#     interface = TsPatternFactory(adapter)
#     cc = interface.create_statements("if x:  print(x)")
#     pp = interface.create_statements("if x:  $body")
#     assert is_match_tree(cc, pp, {})

if __name__ == "__main__":
    unittest.main()

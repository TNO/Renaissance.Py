import unittest

from hamcrest import assert_that, has_length
from parameterized import parameterized

from renaissance.extractors.extractor import Extractor
from renaissance.impl.tree_sitter_adapter.tree_sitter_adapter import TreeSitterAdapter
from renaissance.impl.tree_sitter_adapter.ts_pattern_factory import TsPatternFactory

import tree_sitter_python

from renaissance.syntax_tree.match_finder import is_match, is_match_tree, match_pattern


@parameterized.expand([
    ("def foo(): pass", "def foo(): pass"),
    ("if x:  print(x)", "if x:  $body"),
    ("for i in range(10): print(i)", "for $i in $iter: $body"),
    ("while True: pass", "while $cond: $body"),
    ("try: pass\nexcept Exception: pass", "try: $b\nexcept Exception: $b"),
    ("class A: pass", "class $C: $body"),
    ("with open('x') as f: pass", "with $ctx as $var: $body"),
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
    ("import os\nx=5", "import $mod $stmt"),
])
def test_python_pattern(code, pattern):
    adapter = TreeSitterAdapter(tree_sitter_python)
    interface = TsPatternFactory(adapter)
    extractor = Extractor(interface, [pattern])
    matches = extractor.run(code)

    assert_that(matches, has_length(1), f"{code=} {pattern=}")


def test_is_match_python_patterns():
    adapter = TreeSitterAdapter(tree_sitter_python)
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("try: pass\nexcept Exception: pass")
    p = interface.create_statement("try: $b\nexcept Exception: $b")
    assert is_match(c.children[0], p.children[0], {})  # type: ignore
    assert is_match(c.children[1], p.children[1], {})  # type: ignore
    assert is_match(c.children[2], p.children[2], {})  # type: ignore
    assert is_match(c.children[3], p.children[3], {})  # type: ignore


def test_is_match_python_patterns_tree():
    adapter = TreeSitterAdapter(tree_sitter_python)
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("try: pass\nexcept Exception: pass")
    p = interface.create_statement("try: $b\nexcept Exception: $b")
    assert is_match_tree(c.children, p.children, {})


def test_is_match_python_patterns_1():
    adapter = TreeSitterAdapter(tree_sitter_python)
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("if x:  print(x)")
    p = interface.create_statement("if x:  $body")
    assert_that(is_match(c,p))
    assert match_pattern([c], [p])  # type: ignore

def test_is_match():
    adapter = TreeSitterAdapter(tree_sitter_python)
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("def foo(): pass")
    p = interface.create_statement("def foo(): pass")
    assert_that(is_match(c,p))
# def test_python_patterns_tree_1(self):
#     adapter = TreeSitterAdapter(tspython)
#     interface = TsPatternFactory(adapter)
#     cc = interface.create_statements("if x:  print(x)")
#     pp = interface.create_statements("if x:  $body")
#     assert is_match_tree(cc, pp, {})

if __name__ == "__main__":
    unittest.main()

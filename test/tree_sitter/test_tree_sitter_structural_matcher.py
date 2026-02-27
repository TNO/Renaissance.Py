import unittest

import pytest
import tree_sitter_python as tspython
import tree_sitter_cpp as tscpp

from renaissance.impl.tree_sitter_adapter.tree_sitter_adapter import TreeSitterAdapter
from renaissance.syntax_tree import MatchFinder


@pytest.mark.parametrize("code, pattern", [
        ("def foo(): pass", "def $foo(): pass"),
        ("if x: pass", "if $x: pass"),
        ("for x in y: pass",
            "for $x in $y: pass",
        ),
        ("while x: pass", "while $x: pass"),
        (
            "try: pass except: pass",
            "try: pass except: pass",
        ),
        ("class A: pass", "class $A: pass"),
        ("with x: pass", "with $x: pass"),
        ("assert x", "assert $x"),
        ("return x", "return $x"),
        ("lambda x: x", "lambda $x: $x"),
        ("yield x", "yield $x"),
        ("a = b", "$a = $b"),
        ("a += b", "$a += $b"),
        ("x and y", "$x and $y"),
        ("not x", "not $x"),
        (
            "x if y else z",
            "$x if $y else $z",
        ),
        ("f(x)", "f($x)"),
        ("[x for x in y]", "[x for $x in $y]"),
        ("x in y", "$x in $y"),
        ("import os", "import $os"),
])

def test_python_patterns(code, pattern):
    adapter = TreeSitterAdapter(tspython)
    ast = adapter.parse_code(code)
    lst = adapter.to_lst(code, ast)

    pat = adapter.to_lst(pattern,ast)

    result = MatchFinder.find_all(lst.root.children, pat.root.children).to_list()
    assert  len(result) >= 1

@pytest.mark.parametrize("code, pattern", [
            (
                "int main() { return 0; }",
                "int $main() { return 0; }",
            ),
            ("int a;", "int $a;"),
            ("int b = 1;", "int $b = 1;"),
            ("struct A {};", "struct $A {};"),
            ("class B {};", "class $B {};"),
            ("namespace ns {}", "namespace $ns {}"),
            (
                "template <typename T> class C {};",
                "template <typename $T> class $C {};",
            ),
            ("enum E { A };", "enum $E { $A };"),
            (
                "int f(int x) { return x; }",
                "int $f(int $x) { return $x; }",
            ),
            (
                "void g() { int x = 1; }",
                "void $g() { int $x = 1; }",
            ),
            ("if (x) {}", "if ($x) {}"),
            ("for (;;) {}", "for (;;) {}"),
            ("while (1) {}", "while (1) {}"),
            ("do {} while (0);", "do {} while (0);"),
            (
                "switch(x) { case 1: break; }",
                "switch($x) { case 1: break; }",
            ),
            ("try {} catch (...) {}", "try {} catch (...) {}"),
            ("a + b", "$a + $b"),
            ("-a", "-$a"),
            ("a == b", "$a == $b"),
            ("a != b", "$a != $b"),
            ("a < b", "$a < $b"),
            ("a <= b", "$a <= $b"),
            ("a > b", "$a > $b"),
            ("a >= b", "$a >= $b"),
            ("a && b", "$a && $b"),
            ("a || b", "$a || $b"),
            ("!a", "!$a"),
            ("a = b;", "$a = $b;"),
            ("foo();", "$foo();"),
            # Expressions followed by semicolons and assignments without semicolons
            # make the parser fail, so we skip them for now
        ])
def test_cpp_patterns(code, pattern):
    adapter = TreeSitterAdapter(tscpp)
    ast = adapter.parse_code(code)
    lst = adapter.to_lst(code, ast)
    pat = adapter.to_lst(pattern, ast)

    result = MatchFinder.find_all(lst.root.children, pat.root.children).to_list()
    assert len(result) == 1

if __name__ == "__main__":
    unittest.main()

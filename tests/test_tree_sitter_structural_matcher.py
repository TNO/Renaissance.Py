import unittest
import tree_sitter_python as tspython
import tree_sitter_cpp as tscpp
from lst.lst import LST, LSTNode
from adapters.tree_sitter_adapter import TreeSitterAdapter

from matchers.pattern_matcher import StructuralPatternMatcher


def make_pattern(code: str, adapter: any) -> LSTNode:
    tree = adapter.parse_code(code)
    root = adapter.to_lst(code, tree)
    return root.root


class TestStructuralPatternMatcher(unittest.TestCase):

    def run_match(self, adapter, code: str, pattern_node: LSTNode):
        tree = adapter.parse_code(code) if hasattr(adapter, "parse_code") else None
        lst = adapter.to_lst(code, tree) if tree else adapter.parse("temp.cpp")
        matcher = StructuralPatternMatcher(pattern_node)
        return matcher.match(lst.root)

    def test_python_patterns(self):
        adapter = TreeSitterAdapter(tspython)
        patterns = [
            ("def foo(): pass", make_pattern("def __PLH_foo(): pass", adapter)),
            ("if x: pass", make_pattern("if __PLH_x: pass", adapter)),
            (
                "for x in y: pass",
                make_pattern("for __PLH_x in __PLH_y: pass", adapter),
            ),
            ("while x: pass", make_pattern("while __PLH_x: pass", adapter)),
            (
                "try: pass except: pass",
                make_pattern("try: pass except: pass", adapter),
            ),
            ("class A: pass", make_pattern("class __PLH_A: pass", adapter)),
            ("with x: pass", make_pattern("with __PLH_x: pass", adapter)),
            ("assert x", make_pattern("assert __PLH_x", adapter)),
            ("return x", make_pattern("return __PLH_x", adapter)),
            ("lambda x: x", make_pattern("lambda __PLH_x: __PLH_x", adapter)),
            ("yield x", make_pattern("yield __PLH_x", adapter)),
            ("a = b", make_pattern("__PLH_a = __PLH_b", adapter)),
            ("a += b", make_pattern("__PLH_a += __PLH_b", adapter)),
            ("x and y", make_pattern("__PLH_x and __PLH_y", adapter)),
            ("not x", make_pattern("not __PLH_x", adapter)),
            (
                "x if y else z",
                make_pattern("__PLH_x if __PLH_y else __PLH_z", adapter),
            ),
            ("f(x)", make_pattern("f(__PLH_x)", adapter)),
            ("[x for x in y]", make_pattern("[x for __PLH_x in __PLH_y]", adapter)),
            ("x in y", make_pattern("__PLH_x in __PLH_y", adapter)),
            ("import os", make_pattern("import __PLH_os", adapter)),
        ]
        for code, pattern in patterns:
            with self.subTest(code=code):
                matches = self.run_match(adapter, code, pattern)
                self.assertTrue(len(matches) >= 1)

    def test_cpp_patterns(self):
        adapter = TreeSitterAdapter(tscpp)

        patterns = [
            (
                "int main() { return 0; }",
                make_pattern("int __PLH_main() { return 0; }", adapter),
            ),
            ("int a;", make_pattern("int __PLH_a;", adapter)),
            ("int b = 1;", make_pattern("int __PLH_b = 1;", adapter)),
            ("struct A {};", make_pattern("struct __PLH_A {};", adapter)),
            ("class B {};", make_pattern("class __PLH_B {};", adapter)),
            ("namespace ns {}", make_pattern("namespace __PLH_ns {}", adapter)),
            (
                "template <typename T> class C {};",
                make_pattern("template <typename __PLH_T> class __PLH_C {};", adapter),
            ),
            ("enum E { A };", make_pattern("enum __PLH_E { __PLH_A };", adapter)),
            (
                "int f(int x) { return x; }",
                make_pattern("int __PLH_f(int __PLH_x) { return __PLH_x; }", adapter),
            ),
            (
                "void g() { int x = 1; }",
                make_pattern("void __PLH_g() { int __PLH_x = 1; }", adapter),
            ),
            ("if (x) {}", make_pattern("if (__PLH_x) {}", adapter)),
            ("for (;;) {}", make_pattern("for (;;) {}", adapter)),
            ("while (1) {}", make_pattern("while (1) {}", adapter)),
            ("do {} while (0);", make_pattern("do {} while (0);", adapter)),
            (
                "switch(x) { case 1: break; }",
                make_pattern("switch(__PLH_x) { case 1: break; }", adapter),
            ),
            ("try {} catch (...) {}", make_pattern("try {} catch (...) {}", adapter)),
            ("a + b", make_pattern("__PLH_a + __PLH_b", adapter)),
            ("-a", make_pattern("-__PLH_a", adapter)),
            ("a == b", make_pattern("__PLH_a == __PLH_b", adapter)),
            ("a != b", make_pattern("__PLH_a != __PLH_b", adapter)),
            ("a < b", make_pattern("__PLH_a < __PLH_b", adapter)),
            ("a <= b", make_pattern("__PLH_a <= __PLH_b", adapter)),
            ("a > b", make_pattern("__PLH_a > __PLH_b", adapter)),
            ("a >= b", make_pattern("__PLH_a >= __PLH_b", adapter)),
            ("a && b", make_pattern("__PLH_a && __PLH_b", adapter)),
            ("a || b", make_pattern("__PLH_a || __PLH_b", adapter)),
            ("!a", make_pattern("!__PLH_a", adapter)),
            ("a = b;", make_pattern("__PLH_a = __PLH_b;", adapter)),
            ("foo();", make_pattern("__PLH_foo();", adapter)),
            # Expressions followed by semicolons and assignments without semicolons
            # make the parser fail, so we skip them for now
        ]
        for code, pattern in patterns:
            with self.subTest(code=code):
                matches = self.run_match(adapter, code, pattern)
                self.assertTrue(len(matches) >= 1)


if __name__ == "__main__":
    unittest.main()

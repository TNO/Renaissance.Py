import unittest

from parameterized import parameterized

from lst.lst import LSTNode
from adapters.tree_sitter_adapter import TreeSitterAdapter
import tree_sitter_python as tspython


class TestConcretePatternMatcher(unittest.TestCase):

    def setUp(self):
        self.adapter = TreeSitterAdapter(tspython)
        self.interface = PatternMatcherInterfaceExtended(self.adapter)

    def run_pattern(self, code: str, pattern: str) -> list:
        extractor = Extractor(self.interface)
        extractor.add_rule((pattern, "pattern"), lambda m: m)
        return extractor.run(code)

    @parameterized.expand([
        ("def foo(): pass", "def foo(): pass"),
        ("if x:  print(x)", "if x:  __PLH_body"),
        ("for i in range(10): print(i)", "for __PLH_i in __PLH_iter: __PLH_body"),
        ("while True: pass", "while __PLH_cond: __PLH_body"),
        # ("try: pass except: pass", "try: __PLH_b except: __PLH_b"),
        ("class A: pass", "class __PLH_C: __PLH_body"),
        (
            "with open('x') as f: pass",
            "with __PLH_ctx as __PLH_var: __PLH_body",
        ),
        ("assert x", "assert __PLH_cond"),
        ("return x", "return __PLH_value"),
        ("lambda x: x", "lambda __PLH_arg: __PLH_body"),
        ("a = b", "__PLH_lhs = __PLH_rhs"),
        ("a += b", "__PLH_lhs += __PLH_rhs"),
        ("x and y", "__PLH_left and __PLH_right"),
        ("not x", "not __PLH_expr"),
        ("x if y else z", "__PLH_t if __PLH_cond else __PLH_f"),
        ("f(x)", "__PLH_func(__PLH_arg)"),
        ("[x for x in y]", "[__PLH_x for __PLH_x in __PLH_y]"),
        ("x in y", "__PLH_x in __PLH_y"),
        ("import os", "import __PLH_mod"),
    ])
    def test_python_patterns(self, src, pattern):
        matches = self.run_pattern(src, pattern)
        self.assertTrue(len(matches) >= 1, f"Pattern failed: {pattern}")


if __name__ == "__main__":
    unittest.main()

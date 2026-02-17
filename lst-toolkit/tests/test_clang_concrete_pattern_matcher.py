import unittest

import pytest
from extractors.extractor import PatternMatcherInterfaceExtended, Extractor
from impl.clang.clang_adapter import ClangAdapter
from impl.tree_sitter_adapter.ts_pattern_factory import TsPatternFactory


@pytest.mark.parametrize("code, pattern",[
        ("int main() { return 0; }", "int main() { $body }"),
        ("int add(int a, int b) { return a + b; }", "int $f(int $a, int $b) { $body }"),
        ("void f() { int x = 0; }", "void $name() { $body }"),
        ("if (x) { y(); }", "if ($cond) { $body }"),
        ("for (;;) {}", "for ($init; $cond; $inc) $body"),
        ("while (x) {}", "while ($cond) $body"),
        ("do {} while (x);", "do $body while ($cond);"),
        ("switch(x) { case 1: break; }", "switch ($val) { $cases }"),
        ("try {} catch (...) {}", "try $body catch (...) $handler"),
        ("a = b;", "$lhs = $rhs;"),
        ("x + y;", "$a + $b;"),
        ("-x;", "-$x;"),
        ("foo();", "$f();"),
        ("class A {};", "class $C {};"),
        ("struct B { int x; };", "struct $S { $body };"),
        ("namespace ns {}", "namespace $ns {}"),
        ("template <typename T> class C {};", "template <typename T> class $C {};"),
        ("enum E { A };", "enum $E { $vals };"),
        ("auto f = []() { return 1; };", "auto $f = []() { $body };")
    ])
def test_clang_patterns(code, pattern):
    adapter = ClangAdapter()
    interface = TsPatternFactory(adapter)
    extractor = Extractor(interface)
    extractor.add_rule(pattern, lambda m: m)
    matches = extractor.run(code)
    assert  len(matches) >= 1


if __name__ == "__main__":
    unittest.main()

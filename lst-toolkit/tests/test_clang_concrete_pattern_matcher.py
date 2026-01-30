import unittest
from pathlib import Path

from adapters.clang_adapter import ClangAdapter
from extractors.extractor import PatternMatcherInterfaceExtended, Extractor


# from pathlib import Path
# from clang_adapter import ClangAdapter
# from pattern_matcher import MatchResult
# from match import Match
# from extractor import PatternMatcherInterfaceExtended
# from extractor import Extractor


class TestClangConcretePatterns(unittest.TestCase):

    def setUp(self):
        self.adapter = ClangAdapter()
        self.interface = PatternMatcherInterfaceExtended(self.adapter)

    def run_pattern(self, code: str, pattern: str) -> list:
        Path("temp.cpp").write_text(code)
        extractor = Extractor(self.interface)
        extractor.add_rule((pattern, "pattern"), lambda m: m)
        return extractor.run(code)

    def test_clang_patterns(self):
        patterns = [
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
        ]
        for code, pattern in patterns:
            with self.subTest(code=code):
                matches = self.run_pattern(code, pattern)
                self.assertTrue(len(matches) >= 1, f"Pattern failed: {pattern}")


if __name__ == "__main__":
    unittest.main()

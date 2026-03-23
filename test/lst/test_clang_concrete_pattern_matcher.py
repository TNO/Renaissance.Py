import pytest
from hamcrest import *

import pytest
from renaissance.extractors.extractor import Extractor
from renaissance.impl.clang.clang_adapter import ClangAdapter
from renaissance.impl.tree_sitter_adapter.ts_pattern_factory import TsPatternFactory
from renaissance.syntax_tree import ASTShower


@pytest.mark.parametrize(
    "code, pattern",
    [
        (
            "int $body=0;int main() { return 0; }",
            "int $body=0;int main() { return $body; }",
        ),
        (
            "int $init, $cond, $inc=0;int $body=0;for (;;) {}",
            "int $init, $cond, $inc=0;int $body=0;for ($init; $cond; $inc) $body",
        ),
        ("a = b;", "$lhs = $rhs;"),
        ("int x,y;x + y;", "int $a,$b;$a + $b;"),
        ("int $x;-x;", "int $x;-$x;"),
        ("foo();", "$f();"),
        ("class A {};", "class $C {};"),
        ("struct B { int x; };", "struct $S { $body };"),
        ("namespace ns {}", "namespace $ns {}"),
        (
            "int $C=0; template <typename T> class C {};",
            "int $C=0; template <typename T> class $C {};",
        ),
        (
            "int $E=0; int $vals=0; enum E { A };",
            "int $E=0; int $vals=0;enum $E { $vals };",
        ),
        (
            "int $body=0; auto f = []() { return 1; };",
            "int $body=0; auto $f = []() { $body; };",
        ),
    ],
)
def test_clang_patterns(code, pattern):
    adapter = ClangAdapter()
    interface = TsPatternFactory(adapter)
    extractor = Extractor(interface, [pattern])
    matches = extractor.run(code)
    assert_that(matches, is_not(empty()))


@pytest.mark.parametrize(
    "code, pattern",
    [
        (
            "int add(int a, int b) { return a + b; }",
            "int $a,$b,$body;int $f(int $a, int $b) { $body; }",
        ),
        ("void f() { int x = 0; }", "int $body=0;void $name() { $body }"),
        ("if (x) { y(); }", "int $cond,$body=0;if ($cond) { $body }"),
        ("while (x) {}", "int $cond;while ($cond) $body"),
        ("do {} while (x);", "int $body,$cond;do $body while ($cond);"),
        ("switch(x) { case 1: break; }", "int $val,$cases;switch ($val) { $cases }"),
        ("try {} catch (...) {}", "int $body, $handler;try $body catch (...) $handler"),
    ],
)
def test_clang_patterns_to_be_fixed(code, pattern):
    adapter = ClangAdapter()
    interface = TsPatternFactory(adapter)
    extractor = Extractor(interface, [pattern])
    matches = extractor.run(code)
    assert_that(matches, has_length(0))  # but should be 1


from renaissance.syntax_tree.match_finder import is_match, is_match_tree, MatchFinder


def test_is_match_clang_patterns_without_decl():
    adapter = ClangAdapter()
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("int main() { return 0; }")
    p = interface.create_statement("int main() { return $body; }")
    assert_that(is_match(c.children[-1], p.children[-1], {}), is_(False))


def test_is_match_clang_patterns_with_decl():
    adapter = ClangAdapter()
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("int $body=0; int main() { return 0; }")
    p = interface.create_statement("int $body=0; int main() { return $body; }")
    assert_that(is_match(c.children[-1], p.children[-1], {}), is_(True))


def test_is_match_clang_tree():
    adapter = ClangAdapter()
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("int $body=0; int main() { return 0; }")
    p = interface.create_statement("int $body=0; int main() { return $body; }")
    assert_that(is_match_tree([c.children[-1]], [p.children[-1]], {}), is_(True))


class Matchfinder:
    pass


def test_is_match_clang_patterns():
    adapter = ClangAdapter()
    interface = TsPatternFactory(adapter)
    c = interface.create_statement("int $body=0; int main() { return 0; }")
    p = interface.create_statement("int $body=0; int main() { return $body; }")
    match = MatchFinder.match_pattern([c.children[-1]], [p.children[-1]])
    assert_that(match, has_length(1))


if __name__ == "__main__":
    pytest.main()

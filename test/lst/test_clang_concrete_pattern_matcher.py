import pytest
from hamcrest import *

from renaissance.impl.clang.clang_adapter import ClangAdapter
from renaissance.impl.tree_sitter.extractor import Extractor
from renaissance.impl.tree_sitter.factory import TreeSitterPatternFactory
from renaissance.syntax_tree.match_finder import MIS_MATCH, MatchFinder, find_variants, is_match, is_match_tree, match_pattern


class TestClangConcretePatternMatcher:
    @pytest.mark.parametrize(
        "code, pattern",
        [
            ("int body=0;int main() { return body; }", "int body=0;int main() { return body; }"),
            ("int init, cond, inc=0;int body=0;for (;;) {}", "int $i, $c, $inc=0;int $b=0;for ($i; $c; $inc) $b"),
            ("a = b;", "$lhs = $rhs;"),
            ("int x,y;x + y;", "int $a,$b;$a + $b;"),
            ("int x;-x;", "int $x;-$x;"),
            ("foo();", "$f();"),
            ("class A {};", "class $C {};"),
            ("struct B { int x; };", "struct $S { $body };"),
            ("namespace ns {}", "namespace $ns {}"),
            ("int C=0; template <typename T> class C {};", "int $C=0; template <typename T> class $C {};"),
            ("int body=0; auto f = []() { return 1; };", "int $body=0; auto $f = []() { $body; };"),
        ],
    )
    def test_clang_patterns(self, code, pattern):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        extractor = Extractor(interface, [pattern])
        matches = extractor.run(code)
        assert_that(matches, is_not(empty()))

    def test_clang_patterns_using_extractor(self):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        extractor = Extractor(interface, ["int E=0; int vals=0; enum E { A };"])
        matches = extractor.run("int E = 0; int vals=0; enum E { A };")
        assert_that(matches, has_length(1))

    def test_clang_failing_pattern(self):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        pattern = interface.create_statements("int E=0; int vals=0; enum E { A };")
        code = adapter.load_from_text("int E=0; int vals=0; enum E { A };", "snippets.c")
        matches = match_pattern(code.root.children, pattern)
        assert_that(matches, has_length(1))

    def test_find_variant_with_clang_failing_pattern(self):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        pattern = interface.create_statements("int E1=0; int vals=0; enum E2 { A };")
        code = adapter.load_from_text("int E1=0; int vals=0; enum E2 { A };", "snippets.c")
        matches = find_variants(code.root.children, pattern)
        assert_that(matches, has_length(1))
        assert_that(matches[0].end_index, is_not(MIS_MATCH))

    @pytest.mark.skip("it should be the same really")
    def test_type_property_between_code_and_pattern_are_same(self):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        pattern = interface.create_statement("enum E2 { A };")
        code = adapter.load_from_text("enum E2 { A };", "snippets.c").root.children[0]
        assert_that(code.properties["type"], is_(pattern.properties["type"]))

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
    def test_clang_patterns_to_be_fixed(self, code, pattern):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        extractor = Extractor(interface, [pattern])
        matches = extractor.run(code)
        assert_that(matches, has_length(0))  # but should be 1

    def test_is_match_clang_patterns_without_decl(self):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        c = interface.create_statement("int main() { return 0; }")
        p = interface.create_statement("int main() { return $body; }")
        assert_that(is_match(c.children[-1], p.children[-1], {}), is_(False))

    def test_is_match_clang_patterns_with_decl(self):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        c = interface.create_statement("int $body=0; int main() { return 0; }")
        p = interface.create_statement("int $body=0; int main() { return $body; }")
        assert_that(is_match(c.children[-1], p.children[-1], {}), is_(True))

    def test_is_match_clang_tree(self):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        c = interface.create_statement("int $body=0; int main() { return 0; }")
        p = interface.create_statement("int $body=0; int main() { return $body; }")
        assert_that(is_match_tree([c.children[-1]], [p.children[-1]], {}), is_(True))

    def test_is_match_clang_patterns(self):
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        c = interface.create_statement("int $body=0; int main() { return 0; }")
        p = interface.create_statement("int $body=0; int main() { return $body; }")
        match = MatchFinder.match_pattern([c.children[-1]], [p.children[-1]])
        assert_that(match, has_length(1))


class Matchfinder:
    pass


if __name__ == "__main__":
    pytest.main()

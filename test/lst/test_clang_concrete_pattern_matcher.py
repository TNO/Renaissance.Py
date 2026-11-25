# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for concrete (LST-level) pattern matching against Clang-parsed C++ code."""

import pytest
from hamcrest import assert_that, has_length, is_

from renaissance.core.match import MatchFinder, is_match, match_pattern
from renaissance.core.match.match_finder import find_variants
from renaissance.integrations.clang.clang_adapter import ClangAdapter
from renaissance.parser_bindings.tree_sitter import TreeSitterPatternFactory
from test.unit.shared.utils_for_tests import is_match_tree


class TestClangConcretePatternMatcher:
    """AI: Tests concrete (LST-level) pattern matching against Clang-parsed C++ code."""

    @pytest.mark.parametrize(
        ("code_txt", "pattern_txt"),
        [
            ("int E = 0; int vals=0; enum E { A };", "int E=0; int vals=0; enum E { A };"),
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
    def test_clang_patterns(self, code_txt, pattern_txt) -> None:
        """AI: Verify a variety of C++ constructs match their corresponding pattern with placeholders."""
        adapter = ClangAdapter()
        factory = TreeSitterPatternFactory(adapter)
        pattern = factory.create_statements(pattern_txt)
        code = factory.create_statements(code_txt)
        matches = match_pattern(code, pattern, recursive=False)
        assert_that(matches, has_length(1))

    def test_clang_failing_pattern(self) -> None:
        """AI: Verify an enum statement pattern matches its occurrence via match_pattern directly on LST nodes."""
        # TODO(pjljvandelaar): Why is "failing" in the name of this test function? The match succeeds - has length 1.
        #  @Jinmin Hu: How would you describe the scenario?
        #  What about renaming this test to test_clang_pattern_matches_code_parsed_from_file?
        #  https://github.com/TNO/Renaissance.Py/issues/187
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        pattern = interface.create_statements("int E=0; int vals=0; enum E { A };")
        code = adapter.load_from_text("int E=0; int vals=0; enum E { A };", "snippets.c")
        matches = match_pattern(code.root.children, pattern)
        assert_that(matches, has_length(1))

    def test_find_variant_with_clang_failing_pattern(self) -> None:
        """AI: Verify find_variants locates a matching variant for an enum statement pattern."""
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        statements = "int E1=0; int vals=0; enum E2 { A };"
        pattern = interface.create_statements(statements)
        code = adapter.load_from_text(statements, "snippets.c")
        matches = find_variants(code.root.children, pattern)
        assert_that(matches, has_length(1))
        assert_that(matches[0].index, is_(len(pattern)))

    @pytest.mark.skip("it should be the same really")
    def test_type_property_between_code_and_pattern_are_same(self) -> None:
        """AI: Verify the 'type' property is the same for equivalent code and pattern enum nodes."""
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        pattern = interface.create_statement("enum E2 { A };")
        code = adapter.load_from_text("enum E2 { A };", "snippets.c").root.children[0]
        assert_that(code.properties["type"], is_(pattern.properties["type"]))

    @pytest.mark.parametrize(
        ("code_txt", "pattern_txt"),
        [
            (
                "int add(int a, int b) { return a + b; }",
                "int $a,$b,$body;int $f(int $a, int $b) { $body; }",
            ),
            ("void f() { int x = 0; }", "int $body=0;void $name() { $body }"),
            # TODO(pjljvandelaar): 1. code doesn't start with declaration, so shouldn't match the pattern.
            #  2. In CDT $body in the compound statement should be appended with the terminator (;).
            #  https://github.com/TNO/Renaissance.Py/issues/187
            ("if (x) { y(); }", "int $cond,$body=0;if ($cond) { $body }"),
            ("while (x) {}", "int $cond;while ($cond) $body"),
            ("do {} while (x);", "int $body,$cond;do $body while ($cond);"),
            ("switch(x) { case 1: break; }", "int $val,$cases;switch ($val) { $cases }"),
            ("try {} catch (...) {}", "int $body, $handler;try $body catch (...) $handler"),
            # TODO(pjljvandelaar): 1. Is explicit declaration within the pattern necessary?
            #  Can't it be inferred and implicitly added by the tool chain?
            #  2. Why do some patterns only declare the placeholders, while others initialize them as well?
            #  https://github.com/TNO/Renaissance.Py/issues/187
        ],
    )
    def test_clang_patterns_to_be_fixed(self, code_txt: str, pattern_txt: str) -> None:
        """AI: Verify currently-unsupported C++ constructs don't match their pattern yet (documents known gaps)."""
        adapter = ClangAdapter()
        factory = TreeSitterPatternFactory(adapter)
        pattern = factory.create_statements(pattern_txt)
        code = factory.create_statements(code_txt)
        matches = match_pattern(code, pattern, recursive=False)
        assert_that(matches, has_length(0))  # but should be 1

    def test_is_match_clang_patterns_without_decl(self) -> None:
        """AI: Verify a return statement doesn't match a placeholder pattern when the placeholder isn't declared."""
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        c = interface.create_statement("int main() { return 0; }")
        p = interface.create_statement("int main() { return $body; }")
        assert_that(is_match(c.children[-1], p.children[-1], {}), is_(False))

    def test_is_match_clang_patterns_with_decl(self) -> None:
        """AI: Verify a return statement matches a placeholder pattern when the placeholder is declared."""
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        c = interface.create_statement("int $body=0; int main() { return 0; }")
        p = interface.create_statement("int $body=0; int main() { return $body; }")
        assert_that(is_match(c.children[-1], p.children[-1], {}), is_(True))

    def test_is_match_clang_tree(self) -> None:
        """AI: Verify is_match_tree confirms a matching statement tree against its pattern."""
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        c = interface.create_statement("int $body=0; int main() { return 0; }")
        p = interface.create_statement("int $body=0; int main() { return $body; }")
        assert_that(is_match_tree([c.children[-1]], [p.children[-1]], {}), is_(True))

    def test_is_match_clang_patterns(self) -> None:
        """AI: Verify MatchFinder.match_pattern finds one match for a statement against its pattern."""
        adapter = ClangAdapter()
        interface = TreeSitterPatternFactory(adapter)
        c = interface.create_statement("int $body=0; int main() { return 0; }")
        p = interface.create_statement("int $body=0; int main() { return $body; }")
        match = MatchFinder.match_pattern([c.children[-1]], [p.children[-1]])
        assert_that(match, has_length(1))

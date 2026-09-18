"""Tests for matching AST patterns containing placeholder variants."""

import ast
import textwrap

import pytest
from hamcrest import (
    assert_that,
    calling,
    empty,
    has_length,
    is_,
    is_not,
    less_than,
    raises,
)

from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree import ASTFactory, ASTShower
from renaissance.syntax_tree.match_finder import (
    MatchFinder,
    find_in_list,
    is_match,
    is_match_tree,
    match_pattern,
    variant_in_match_stmt,
)


class TestMatchTree:
    """AI: Tests for matching AST patterns containing placeholder variants."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """AI: Build the shared Python factory and pattern factory used by the match-tree tests."""
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_none_with_none_is_not_allowed(self):
        """AI: Verify is_match_tree raises when both source and pattern are None."""
        assert_that(calling(lambda: is_match_tree(None, None)), raises(Exception))

    def test_none_with_list(self):
        """AI: Verify is_match_tree raises when the source is None but the pattern is a list."""
        pattern = self.pattern_factory.create_statements("1")

        assert_that(calling(lambda: is_match_tree(None, pattern)), raises(Exception))

    def test_list_with_none(self):
        """AI: Verify is_match_tree returns False when the source is a list but the pattern is None."""
        src = self.pattern_factory.create_statements("1")
        pattern = None

        assert_that(is_match_tree(src, pattern), is_(False))

    def test_empty_lists_with_empty_pattern(self):
        """AI: Verify is_match_tree returns True for two empty lists."""
        src = []
        pattern = []

        assert_that(is_match_tree(src, pattern), is_(True))

    def test_lists_with_empty_pattern(self):
        """AI: Verify is_match_tree returns False when the source is non-empty but the pattern is empty."""
        src = self.pattern_factory.create_statements("1")
        pattern = []

        assert_that(is_match_tree(src, pattern), is_(False))

    def test_is_match_tree_between_list_and_other(self):
        """AI: Verify is_match_tree returns False when the pattern list contains a raw non-node object."""
        src = self.pattern_factory.create_statements("1")
        pattern = ast.Name("name")

        assert_that(is_match_tree(src, [pattern]), is_(False))

    def test_empty_lists_with_pattern(self):
        """AI: Verify is_match_tree returns False when the source is empty but the pattern is non-empty."""
        src = []
        pattern = self.pattern_factory.create_statements("1")

        assert_that(is_match_tree(src, pattern), is_(False))

    def test_lists_with_list(self):
        """AI: Verify is_match_tree matches when source and pattern are identical statement lists."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")

        assert_that(is_match_tree(src, pattern), is_(True))

    def test_lists_with_matcher(self):
        """AI: Verify is_match_tree matches any statement list against a bare multi-placeholder pattern."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$name")

        assert_that(is_match_tree(src, pattern), is_(True))

    def test_lists_with_list_with_matcher_at_end(self):
        """AI: Verify is_match_tree matches when a multi-placeholder trails a fixed prefix."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("1\n2\n$$name")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_at_start(self):
        """AI: Verify is_match_tree matches when a multi-placeholder leads a fixed suffix."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$name\n5\n6")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_multi_single(self):
        """AI: Verify a multi-placeholder followed by a single-placeholder captures the expected split of statements."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$name\n$name")
        exp = {}

        assert_that(is_match_tree(src, pattern, exp))

        assert_that(exp["$$name"], has_length(5))
        assert_that(exp["$name"], has_length(1))

    def test_lists_with_list_with_list_multi_single(self):
        """AI: Verify a fixed prefix, multi-placeholder, then single-placeholder captures the expected split."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("1\n2\n$$name\n$name")
        exp = {}

        assert_that(is_match_tree(src, pattern, exp), is_(True))

        assert_that(exp["$$name"], has_length(3))
        assert_that(exp["$name"], has_length(1))

    def test_lists_with_list_with_matcher_in_the_middle(self):
        """AI: Verify is_match_tree matches when a multi-placeholder sits between a fixed prefix and suffix."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("1\n$$name\n6")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_both_end(self):
        """AI: Verify is_match_tree matches when multi-placeholders bracket a fixed middle statement."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$start\n3\n$$end")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_both_end_empty_list_at_start(self):
        """AI: Verify is_match_tree matches when the leading multi-placeholder captures zero statements."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$start\n1\n$$end")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_both_end_empty_list_at_the_end(self):
        """AI: Verify is_match_tree matches when the trailing multi-placeholder captures zero statements."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$start\n6\n$$end")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_both_end__mismatch(self):
        """AI: Verify is_match_tree returns False when two same-named multi-placeholders can't reconcile a mismatched split."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n61\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq")

        assert_that(is_match_tree(src, pattern, {}), is_(False))

    def test_lists_with_list_with_matcher_in_both_end_same_pattern(self):
        """AI: Verify is_match_tree returns False when the source lacks the trailing statement required by the pattern."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n61\n2\n3\n4\n5")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq")

        assert_that(is_match_tree(src, pattern, {}), is_(False))

    def test_lists_with_list_with_matcher_in_matcher_in_between(self):
        """AI: Verify is_match_tree matches a same-named multi-placeholder pair sandwiched between fixed statements."""
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq\n7\n8\n9")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_matcher_in_between_but_has_leftover(self):
        """AI: Verify is_match_tree returns False when trailing source statements are left unmatched after the pattern."""
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq")

        assert_that(is_match_tree(src, pattern, {}), is_(False))

    def test_find_in_list(self):
        """AI: Verify find_in_list returns the index of the first matching statement."""
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("2")

        assert_that(find_in_list(src, pattern, {}), is_(0))

    def test_find_in_list_with_expansion(self):
        """AI: Verify find_in_list returns the match index and populates the expansion dict for a single-placeholder."""
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("2\n$3\n4")
        exp = {}

        assert_that(find_in_list(src, pattern, exp), is_(2))
        assert_that(exp["$3"][0].name, is_("3"))

    def test_can_t_find_in_list(self):
        """AI: Verify find_in_list returns a negative index when the pattern has no match."""
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("1")

        assert_that(find_in_list(src, pattern, {}), less_than(0))

    def test_find_in_list_returns_last_pos(self):
        """AI: Verify find_in_list returns the last valid index when the pattern matches at the end of the list."""
        src = self.pattern_factory.create_statements("0\n1\n2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("0\n1\n2\n3\n4\n5")

        assert_that(find_in_list(src, pattern, {}), is_(5))

    def test_find_with_match_all_returns_last_pos(self):
        """AI: Verify find_in_list returns the last index when the pattern ends with a trailing multi-placeholder."""
        src = self.pattern_factory.create_statements("0\n1\n2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("0\n1\n2\n3\n4\n5\n$$seq")

        assert_that(find_in_list(src, pattern, {}), is_(len(src) - 1))

    def test_lists_with_list_with_matcher_in_both_end_mismatch2(self):
        """AI: Verify is_match_tree returns False when the source is one statement shorter than the pattern requires."""
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n61\n2\n3\n4\n5")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq")
        assert_that(is_match_tree(src, pattern, {}), is_(False))

    def test_find_function_with_any_param_python(self):
        """AI: Verify find_in_list locates a Python call statement against a variadic-argument pattern."""
        atu = self.factory.create_from_text("ca(13,14,15)", "test.py")
        src = atu.children
        pattern = self.pattern_factory.create_statements("ca($$all)")
        assert_that(find_in_list(src, pattern, {}), is_(0))

    def test_find_function_with_any_param_and_all_param_in_python(self):
        """AI: Verify find_in_list locates a Python call statement matched by a single-plus-variadic argument pattern."""
        atu = self.factory.create_from_text("ca(13,14,15)", "test.py")
        src = atu.children
        pattern = self.pattern_factory.create_statements("$f($a,$$all)")
        assert_that(find_in_list(src, pattern, {}), is_(0))

    def test_match_all_function_with_any_param_clang(self):
        """AI: Verify match_pattern finds both matching C function calls against a variadic-argument pattern."""
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text("void ca(int a,int b,int c){ca(13,14,15); ca(13,14,15);}", "fut.c")
        src = atu.children[-1].children[-1].children
        pattern = factory.create_from_text("int $a,$$all;void $f(int a,int b){$f($a, $$all);}", "pat.c").children[-1].children[-1].children
        assert_that(match_pattern(src, pattern), has_length(2))

    def test_find_all_in_list_with_expansion(self):
        """AI: Verify match_pattern finds all matches and captures the single-placeholder expansion for each."""
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("2\n$3\n4")
        matches = match_pattern(src, pattern)
        assert_that(matches, has_length(2))
        assert_that(matches[0].expansions["$3"][0].name, is_("3"))

    def test_find_all_in_python_list_with_expansion(self):
        """AI: Verify match_pattern finds a TestCase subclass and captures its class-name expansion."""
        atu = self.factory.create_from_text(
            textwrap.dedent("""
        from unittest import TestCase

        class TestExample(TestCase):
            def test_case_example(self):
                # arrange
                factory = {}

                # act
                factory['a']= 1

                # assert
                self.assertEqual(len(factory), 1)
        """),
            "test_file.py",
        )
        pattern = self.pattern_factory.create_statement("class $name(TestCase):\n    $$cases")
        ASTShower.show_node(pattern)
        expansions = {}
        variant_in_match_stmt(atu.children[-1], pattern, expansions)
        is_match(atu.children[-1], pattern)
        matches = match_pattern([atu.children[-1]], [pattern])
        assert_that(matches, has_length(1))
        assert_that(matches[0].expansions["$name"][0], is_("TestExample"))

    def test_find_all_in_python_arg_list_with_expansion1(self):
        """AI: Verify match_pattern finds a call matched by a bare variadic-argument pattern and captures a non-empty expansion."""
        self.factory.create_from_text("class klass: pass", "test_file.py")
        statement = self.pattern_factory.create_statements("assertEqual(1,2,34,5,6,7,7,8)")
        pattern = self.pattern_factory.create_statements("assertEqual($$args)")
        matches = match_pattern(statement, pattern)
        assert_that(matches, has_length(1))
        assert_that(matches[0].expansions["$$args"], is_not(empty()))

    def test_find_all_in_python_arg_list_with_expansion2(self):
        """AI: Verify match_pattern finds a function def matched by a variadic-parameter pattern and captures a non-empty expansion."""
        atu = self.factory.create_from_text("class klass:\n  def fun(a,b,c,d,f): pass", "test_file.py")
        pattern = self.pattern_factory.create_statements("def fun($$args): pass")
        matches = match_pattern(atu.children, pattern)
        assert_that(matches, has_length(1))
        assert_that(matches[0].expansions["$$args"], is_not(empty()))

    def test_find_all_in_clang_list_with_expansion(self):
        """AI: Verify match_pattern finds both matching C comparisons and captures a non-empty expansion for the first."""
        factory = ASTFactory(ClangASTNode, [])
        pattern = CPatternFactory(factory).create_statements("a == $x;")
        src = CPatternFactory(factory).create_statements("a == 3;a == 4; b == 5;")
        matches = match_pattern(src, pattern)
        assert_that(matches, has_length(2))
        assert_that(matches[0].expansions["$x"], is_not(empty()))

    @pytest.mark.skip
    def test_match_one_and_all_params(self):
        """AI: Verify MatchFinder.match_pattern finds a keyword-argument call matched by a single kwarg pattern."""
        sample = textwrap.dedent("""
        context_stub=0
        EMRMxAPxData_data_rep = 0
        class SomeTest:
            def setUp(self):
                [].append(
                      TAUT.TestDoubles(module=EMRMxAPxData_data_rep, context=context_stub)
                )
        """)
        atu = self.factory.create_from_text(sample, "sample.py")
        ASTShower.show_node(atu)
        kwargs = self.pattern_factory.create_kwargs("$c=context_stub")
        matches = MatchFinder.match_pattern(atu.children, kwargs)
        assert_that(matches, has_length(1))

    def test_match_pattern_for_parameterized_finds_one_match1(self):
        """AI: Verify match_pattern finds a single @parameterized.expand-decorated test method."""
        code = textwrap.dedent("""
        from parameterized import parameterized

        class TestASTReference:

            @parameterized.expand(Factories.extend())
            def test_definition_declaration_references(self, _, factory, code, *args):
                pass
        """)
        atu = self.factory.create_from_text(code)
        unittest = self.pattern_factory.create_statements("@parameterized.expand($$parameters)\ndef $fun($$args, *$$vargs):\n    $$stmts")
        found = match_pattern(atu.children, unittest)
        assert_that(found, has_length(1))

    def test_match_pattern_for_parameterized_finds_one_match2(self):
        """AI: Verify match_pattern finds one match even when the result is materialized via list()."""
        code = textwrap.dedent("""
        from parameterized import parameterized

        class TestASTReference:

            @parameterized.expand(Factories.extend())
            def test_definition_declaration_references(self, _, factory, code, *args):
                pass
        """)
        atu = self.factory.create_from_text(code)
        unittest = self.pattern_factory.create_statements("@parameterized.expand($$parameters)\ndef $fun($$args, *$$vargs):\n    $$stmts")
        found = list(match_pattern(atu.children, unittest))
        assert_that(found, has_length(1))

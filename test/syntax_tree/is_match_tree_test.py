import ast
import textwrap

import pytest
from hamcrest import (
    assert_that,
    has_length,
    is_,
    not_none,
    empty,
    is_not,
    greater_than,
    less_than,
)
from marshmallow.utils import is_generator

from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.impl.python import PythonPatternFactory, PythonRstNode
from renaissance.impl.python.factory import PythonFactory
from renaissance.syntax_tree import ASTFactory, ASTShower
from renaissance.syntax_tree.match_finder import (
    is_match_tree,
    MatchFinder,
    find_in_list,
    match_pattern,
)


class TestMatchTree:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_none_with_none(self):
        src = None
        pattern = None

        assert_that(is_match_tree(src, pattern), is_(True))

    def test_none_with_list(self):
        src = None
        pattern = self.pattern_factory.create_statements("1")

        assert_that(is_match_tree(src, pattern), is_(False))

    def test_list_with_none(self):
        src = self.pattern_factory.create_statements("1")
        pattern = None

        assert_that(is_match_tree(src, pattern), is_(False))

    def test_empty_lists_with_empty_pattern(self):
        src = []
        pattern = []

        assert_that(is_match_tree(src, pattern), is_(True))

    def test_lists_with_empty_pattern(self):
        src = [1]
        pattern = []

        assert_that(is_match_tree(src, pattern), is_(False))

    def test_is_match_tree_between_list_and_other(self):
        src = self.pattern_factory.create_statements("1")
        pattern = ast.Name("name")

        assert_that(is_match_tree(src, pattern), is_(False))

    def test_empty_lists_with_pattern(self):
        src = []
        pattern = self.pattern_factory.create_statements("1")

        assert_that(is_match_tree(src, pattern), is_(False))

    def test_lists_with_list(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")

        assert_that(is_match_tree(src, pattern), is_(True))

    def test_lists_with_matcher(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$name")

        assert_that(is_match_tree(src, pattern), is_(True))

    def test_lists_with_list_with_matcher_at_end(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("1\n2\n$$name")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_at_start(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$name\n5\n6")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_multi_single(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$name\n$name")
        exp = {}

        assert_that(is_match_tree(src, pattern, exp))

        assert_that(exp["$$name"], has_length(5))
        assert_that(exp["$name"], has_length(1))

    def test_lists_with_list_with_list_multi_single(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("1\n2\n$$name\n$name")
        exp = {}

        assert_that(is_match_tree(src, pattern, exp), is_(True))

        assert_that(exp["$$name"], has_length(3))
        assert_that(exp["$name"], has_length(1))

    def test_lists_with_list_with_matcher_in_the_middle(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("1\n$$name\n6")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_both_end(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$start\n3\n$$end")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_both_end_empty_list_at_start(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$start\n1\n$$end")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_both_end_empty_list_at_the_end(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$start\n6\n$$end")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_both_end__mismatch(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n61\n2\n3\n4\n5\n6")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq")

        assert_that(is_match_tree(src, pattern, {}), is_(False))

    def test_lists_with_list_with_matcher_in_both_end_same_pattern(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n61\n2\n3\n4\n5")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq")

        assert_that(is_match_tree(src, pattern, {}), is_(False))

    def test_lists_with_list_with_matcher_in_matcher_in_between(self):
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq\n7\n8\n9")

        assert_that(is_match_tree(src, pattern, {}), is_(True))

    def test_lists_with_list_with_matcher_in_matcher_in_between_but_has_leftover(self):
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq")

        assert_that(is_match_tree(src, pattern, {}), is_(False))

    def test_find_in_list(self):
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("2")

        assert_that(find_in_list(src, pattern, {}), is_(0))

    def test_find_in_list_with_expansion(self):
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("2\n$3\n4")
        exp = {}

        assert_that(find_in_list(src, pattern, exp), is_(2))
        assert_that(exp["$3"][0].name, is_("3"))

    def test_can_t_find_in_list(self):
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("1")

        assert_that(find_in_list(src, pattern, {}), less_than(0))

    def test_find_in_list_returns_last_pos(self):
        src = self.pattern_factory.create_statements("0\n1\n2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("0\n1\n2\n3\n4\n5")

        assert_that(find_in_list(src, pattern, {}), is_(5))

    def test_find_with_match_all_returns_last_pos(self):
        src = self.pattern_factory.create_statements("0\n1\n2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("0\n1\n2\n3\n4\n5\n$$seq")

        assert_that(find_in_list(src, pattern, {}), is_(len(src) - 1))

    def test_lists_with_list_with_matcher_in_both_end_mismatch2(self):
        src = self.pattern_factory.create_statements("1\n2\n3\n4\n5\n61\n2\n3\n4\n5")
        pattern = self.pattern_factory.create_statements("$$seq\n61\n$$seq")
        assert_that(is_match_tree(src, pattern, {}), is_(False))

    def test_find_function_with_any_param_python(self):
        atu = self.factory.create_from_text("ca(13,14,15)", "test.py")
        src = atu.children
        pattern = self.pattern_factory.create_statements("ca($$all)")
        assert_that(find_in_list(src, pattern, {}), is_(0))

    def test_find_function_with_any_param_and_all_param_in_python(self):
        atu = self.factory.create_from_text("ca(13,14,15)", "test.py")
        src = atu.children
        pattern = self.pattern_factory.create_statements("$f($a,$$all)")
        assert_that(find_in_list(src, pattern, {}), is_(0))

    def test_match_all_function_with_any_param_clang(self):
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text("void ca(int a,int b,int c){ca(13,14,15); ca(13,14,15);}", "fut.c")
        src = atu.children[-1].children[-1].children
        pattern = factory.create_from_text("int $a,$$all;void $f(int a,int b){$f($a, $$all);}", "pat.c").children[-1].children[-1].children
        assert_that(match_pattern(src, pattern), has_length(2))

    def test_find_all_in_list_with_expansion(self):
        src = self.pattern_factory.create_statements("2\n3\n4\n5\n61\n2\n3\n4\n5\n7\n8\n9")
        pattern = self.pattern_factory.create_statements("2\n$3\n4")
        matches = match_pattern(src, pattern)
        assert_that(matches, has_length(2))
        assert_that(matches[0].expansions["$3"][0].name, is_("3"))

    def test_find_all_in_python_list_with_expansion(self):
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
        pattern = self.pattern_factory.create_statements("class $name(TestCase):\n    $$cases")
        ASTShower.show_node(pattern[0])
        matches = match_pattern(atu.children, pattern)
        assert_that(matches, has_length(1))
        assert_that(matches[0].expansions["$name"][0], is_("TestExample"))

    def test_find_all_in_python_arg_list_with_expansion(self):
        atu = self.factory.create_from_text("class klass: pass", "test_file.py")
        statement = self.pattern_factory.create_statements("assertEqual(1,2,34,5,6,7,7,8)")
        pattern = self.pattern_factory.create_statements("assertEqual($$args)")
        matches = match_pattern(statement, pattern)
        assert_that(matches, has_length(1))
        assert_that(matches[0].expansions["$$args"], is_not(empty()))

    def test_find_all_in_python_arg_list_with_expansion(self):
        atu = self.factory.create_from_text("class klass:\n  def fun(a,b,c,d,f): pass", "test_file.py")
        pattern = self.pattern_factory.create_statements("def fun($$args): pass")
        matches = match_pattern(atu.children, pattern)
        assert_that(matches, has_length(1))
        assert_that(matches[0].expansions["$$args"], is_not(empty()))

    def test_find_all_in_clang_list_with_expansion(self):
        factory = ASTFactory(ClangASTNode, [])
        pattern = CPatternFactory(factory).create_statements("a == $x;")
        src = CPatternFactory(factory).create_statements("a == 3;a == 4; b == 5;")
        matches = match_pattern(src, pattern)
        assert_that(matches, has_length(2))
        assert_that(matches[0].expansions["$x"], is_not(empty()))

    def test_match_one_and_all_params(self):
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


    def test_match_pattern_for_parameterized_finds_one_match(self):
        code = textwrap.dedent("""
        from parameterized import parameterized

        class TestASTReference:

            @parameterized.expand(Factories.extend())
            def test_definition_declaration_references(self, _, factory, code, *args):
                pass
        """)
        atu = self.factory.create_from_text(code)
        unittest = self.pattern_factory.create_statements(
            "@parameterized.expand($$parameters)\ndef $fun($$args, *$$vargs):\n    $$stmts")
        found = list(match_pattern(atu.children, unittest))
        assert_that(found, has_length(1))

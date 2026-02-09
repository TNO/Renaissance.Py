import unittest
from unittest import TestCase
from parameterized import parameterized

from c_cpp.factories import Factories
from descendant_search import find_descendant_match


from syntax_tree import CPatternFactory, ASTFactory, MatchFinder
from syntax_tree.match_finder import is_match


class TestFindDescendantMatch(TestCase):

    code_text: str = """
            int my_function();
                                       
            void your_function(int count) {
                int z = my_function();
                if (count > my_function()) {
                    int x = my_function();
                    my_function();
                }
                my_function();
                if (count <= my_function()) {
                    int y = my_function();
                } else {
                    my_function();
                }
                my_function();
            }
            """

    outer_text: str = "if ($cond) { $$stmts; }"
    inner_text: str = "my_function()"
    extra_declarations_inner_text: list[str] = ["int my_function();"]

    @parameterized.expand(Factories.factories)
    def test_descendant_search(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.c")
        outer_pattern = pattern_factory.create_statement(self.outer_text)
        inner_pattern = pattern_factory.create_expression(
            self.inner_text, self.extra_declarations_inner_text
        )
        results = find_descendant_match(
            code_pattern, outer_pattern, inner_pattern
        ).to_list()

        count: int = len(results)
        assert 3 == count, "count = " + str(count)


class TestBasic(TestCase):

    code_text: str = """
            int my_function();
            void your_function() {
                my_function();
            }
            """

    literal_text: str = "my_function()"
    extra_declarations_literal_text: list[str] = ["int my_function();"]

    placeholder_text: str = "$f()"
    extra_declarations_placeholder_text: list[str] = ["int $f();"]

    @parameterized.expand(
        list(
            Factories.extend(
                [
                    (literal_text, extra_declarations_literal_text),
                    (placeholder_text, extra_declarations_placeholder_text),
                ]
            )
        )
    )
    def test_snippet(
        self, _: str, factory: ASTFactory, snippet: str, extra_declarations: list[str]
    ):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(
            self.code_text, "text.c"
        )  # file extension consistent with C Pattern Factory
        snippet_pattern = pattern_factory.create_expression(snippet, extra_declarations)
        results = MatchFinder.find_all(code_pattern, [snippet_pattern]).to_list()
        count: int = len(results)
        assert 1 == count, "count = " + str(count)

    @parameterized.expand(Factories.factories)

    def test_is_match_assignment_expression(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        expression1_pattern = pattern_factory.create_expression("x=3", ["int x;"])
        assert is_match(expression1_pattern, expression1_pattern, {}), "An expression matches itself"

        expression2_pattern = pattern_factory.create_expression("x=3", ["int x;"])
        assert is_match(expression1_pattern, expression2_pattern, {}), "Identical expressions match"


    @parameterized.expand(Factories.factories)
    def test_is_match_call_expression(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        expression1_pattern = pattern_factory.create_expression("f()", ["int f();"])
        assert is_match(expression1_pattern, expression1_pattern,{}), "An expression matches itself"
        
        expression2_pattern = pattern_factory.create_expression("f()", ["int f();"])
        assert is_match(expression1_pattern, expression2_pattern,{}), "Identical expressions match"
        


    @parameterized.expand(Factories.factories)
    @unittest.skip("stmt and expr are the same")
    def test_is_match_expression_differs_from_stmt(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        expression_pattern = pattern_factory.create_expression("x=3", ["int x;"])
        statement_pattern = pattern_factory.create_statement("x=3;", extra_declarations=["int x;"])
        assert not is_match(expression_pattern, statement_pattern, {}), "An expression doesn't match a statement"

        expression_pattern = pattern_factory.create_expression("f()", ["int f();"])
        statement_pattern = pattern_factory.create_statement("f();", extra_declarations=["int f();"])
        assert not is_match(expression_pattern, statement_pattern, {}), "An expression doesn't match a statement"

    @parameterized.expand(Factories.factories)
    def test_is_match_statement(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        statement1_pattern = pattern_factory.create_statement("f();", extra_declarations=["int f();"])
        self.assertTrue( is_match(statement1_pattern, statement1_pattern,{}), "A statement matches itself")
        
        statement2_pattern = pattern_factory.create_statement("f ( ) ;", extra_declarations=["int f();"])
        self.assertTrue(  is_match(statement1_pattern, statement2_pattern), "Identical statements match")

        # expression can be foundwith f(), is match is not exact match
        expression_pattern = pattern_factory.create_expression("f(3)", ["int f();"])
        self.assertFalse(  is_match(statement1_pattern, expression_pattern), "A statement doesn't match an expression")
        
        
   
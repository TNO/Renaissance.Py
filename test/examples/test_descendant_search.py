import pytest
from hamcrest import *

from c_cpp.factories import Factories
from rejuvenation.descendant_search import find_descendant_match
from renaissance.impl.clang import CPatternFactory, ClangASTNode
from renaissance.impl.clang_json import ClangJsonASTNode
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.match_finder import is_match, AstProtocol, match_pattern


class TestFindDescendantMatch:
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

    def test_descendant_search_with_clang(self):
        factory = ASTFactory(ClangASTNode)
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.c")
        outer_pattern = pattern_factory.create_statement(self.outer_text)
        inner_pattern = pattern_factory.create_expression(self.inner_text, self.extra_declarations_inner_text)
        results = find_descendant_match(code_pattern, outer_pattern, inner_pattern)

        assert_that(results, has_length(3), f"length of results = {len(results)}")

    def test_descendant_search_with_json(self):
        factory = ASTFactory(ClangJsonASTNode)
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.c")
        outer_pattern = pattern_factory.create_statement(self.outer_text)
        inner_pattern = pattern_factory.create_expression(self.inner_text, self.extra_declarations_inner_text)
        results = find_descendant_match(code_pattern, outer_pattern, inner_pattern)

        assert_that(results, has_length(3), f"length of results = {len(results)}")


class TestBasic:

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

    @pytest.mark.parametrize(
        "_, factory, snippet, extra_declarations",
        list(
            Factories.extend(
                [
                    (literal_text, extra_declarations_literal_text),
                    (placeholder_text, extra_declarations_placeholder_text),
                ]
            )
        ),
    )
    def test_snippet(self, _: str, factory: ASTFactory, snippet: str, extra_declarations: list[str]):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.c")  # file extension consistent with C Pattern Factory
        snippet_pattern = pattern_factory.create_expression(snippet, extra_declarations)
        results = match_pattern(code_pattern.children, [snippet_pattern])
        assert_that(results, has_length(1), f"length of results = {len(results)}")

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_is_match_assignment_expression(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        expression1_pattern: AstProtocol = pattern_factory.create_expression("x=3", ["int x;"])
        assert_that(
            is_match(expression1_pattern, expression1_pattern, {}),
            is_(True),
            "An expression matches itself",
        )

        expression2_pattern = pattern_factory.create_expression("x=3", ["int x;"])
        assert_that(
            is_match(expression1_pattern, expression2_pattern, {}),
            is_(True),
            "Identical expressions match",
        )

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_is_match_call_expression(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        expression1_pattern = pattern_factory.create_expression("f()", ["int f();"])
        assert_that(
            is_match(expression1_pattern, expression1_pattern, {}),
            is_(True),
            "An expression matches itself",
        )

        expression2_pattern = pattern_factory.create_expression("f()", ["int f();"])
        assert_that(
            is_match(expression1_pattern, expression2_pattern, {}),
            is_(True),
            "Identical expressions match",
        )

    @pytest.mark.parametrize("_, factory", Factories.factories)
    @pytest.mark.skip("stmt and expr are the same")
    def test_is_match_expression_differs_from_stmt(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        expression_pattern = pattern_factory.create_expression("x=3", ["int x;"])
        statement_pattern = pattern_factory.create_statement("x=3;", extra_declarations=["int x;"])
        assert_that(
            is_match(expression_pattern, statement_pattern, {}),
            is_(False),
            "An expression doesn't match a statement",
        )

        expression_pattern = pattern_factory.create_expression("f()", ["int f();"])
        statement_pattern = pattern_factory.create_statement("f();", extra_declarations=["int f();"])
        assert_that(
            is_match(expression_pattern, statement_pattern, {}),
            is_(False),
            "An expression doesn't match a statement",
        )

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_is_match_statement(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        statement1_pattern = pattern_factory.create_statement("f();", extra_declarations=["int f();"])
        assert_that(
            is_match(statement1_pattern, statement1_pattern, {}),
            is_(True),
            "A statement matches itself",
        )

        statement2_pattern = pattern_factory.create_statement("f ( ) ;", extra_declarations=["int f();"])
        assert_that(
            is_match(statement1_pattern, statement2_pattern),
            is_(True),
            "Identical statements match",
        )

        # expression can be found with f(), is match is not exact match
        expression_pattern = pattern_factory.create_expression("f(3)", ["int f();"])
        assert_that(
            is_match(statement1_pattern, expression_pattern),
            is_(False),
            "A statement doesn't match an expression",
        )

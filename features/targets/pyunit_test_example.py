import unittest
from unittest import TestCase
from unittest import TestCase, main
from parameterized import parameterized

from c_cpp.factories import Factories
from rejuvenation.descendant_search import find_descendant_match
from renaissance.impl.clang import CPatternFactory

from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.match_finder import is_match


class TestFindDescendantMatch(unittest.TestCase):

    def setUpClass(cls):
        cls.code_text: str = "int my_function();"
    def setUp(self):
        self.outer_text: str = "if ($cond) { $$stmts; }"
        self.inner_text: str = "my_function()"
        self.extra_declarations_inner_text: list[str] = ["int my_function();"]

    def tearDown(self):
        self.outer_text: str = None
        self.inner_text: str = None
        self.extra_declarations_inner_text = None

    def tearDownClass(cls):
        cls.code_text: str = None


    def test_is_match_assignment_expression(self):
        pattern_factory = CPatternFactory(None)
        expression1_pattern = pattern_factory.create_expression("x=3", ["int x;"])
        #plain assert
        assert is_match(expression1_pattern, expression1_pattern, {}), "An expression matches itself"
        self.assertTrue(is_match(expression1_pattern, expression1_pattern, {}), "A statement matches itself")
        self.assertFalse(is_match('statement1_pattern', expression1_pattern), "A statement doesn't match an expression")

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

        # test length
        count: int = len(results)
        assert 3 == count, "count = " + str(count)

# no namespace
class TestBasicNoNamespace(TestCase):
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

    #parameterised
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
    @unittest.skip("stmt and expr are the same")
    # unused param
    def test_snippet(
            self, _: str, factory: ASTFactory, snippet: str, extra_declarations: list[str]
    ):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(
            self.code_text, "text.c"
        )  # file extension consistent with C Pattern Factory
        snippet_pattern = pattern_factory.create_expression(snippet, extra_declarations)
        results = MatchFinder.find_all(code_pattern.children, [snippet_pattern]).to_list()
        count: int = len(results)
        # plain assert with msg
        assert 1 == count, "count = " + str(count)

def test_it_can_be_created():
    it = PythonASTNode(ast.Pass())
    assert_that(it, is_(not_none()))


def test_it_has_elements():
    it = PythonASTNode(ast.parse('def fun():  pass'))
    assert_that(it[0], is_(it.children[0]))

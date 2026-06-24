import ast
import unittest
from unittest import TestCase
from parameterized import parameterized

from c_cpp.factories import Factories
from renaissance.impl.clang import CPatternFactory
from renaissance.impl.python import PythonRstNode
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.match_finder import (
    match_pattern,
)


class FindMatchTest(unittest.TestCase):

    # def setUpClass(cls):
    #     cls.code_text: str = "int my_function();"
    def setUp(self):
        self.b = 55
        print(f"{self.b=}")
        self.a = 5
        print(f"{self.a=}")
        self.outer_text: str = "if ($cond) { $$stmts; }"
        self.inner_text: str = "my_function()"
        self.code_text: str = "int code(int text){return 0;}"
        self.extra_declarations_inner_text: list[str] = ["int my_function();"]
        if self.extra_declarations_inner_text:
            print(f"{self.extra_declarations_inner_text[0]}")

    def tearDown(self):
        self.outer_text: str = None
        self.inner_text: str = None
        self.extra_declarations_inner_text = None

    # def tearDownClass(cls):
    #     cls.code_text: str = None

    def test_is_match(self):

        # plain assert
        assert self.a in [self.a], "An expression matches itself"

        self.assertEqual(self.a, 5)
        self.assertEqual(55, self.b)
        self.assertTrue(self.a == self.a, "A statement matches itself")
        self.assertFalse("statement1_pattern" == self.a, "A statement doesn't match an expression")

    @parameterized.expand(Factories.factories)
    def test_case(self, _: str, factory: ASTFactory):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.c")
        outer_pattern = pattern_factory.create_statement(self.outer_text)
        inner_pattern = pattern_factory.create_expression(self.inner_text, self.extra_declarations_inner_text)
        results = match_pattern([code_pattern], [outer_pattern])

        # test length
        count: int = len(results)
        assert 0 == count, "count = " + str(count)


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

    # parameterised
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
    def test_snippet(self, _: str, factory: ASTFactory, snippet: str, extra_declarations: list[str]):
        pattern_factory = CPatternFactory(factory)
        code_pattern = factory.create_from_text(self.code_text, "text.c")  # file extension consistent with C Pattern Factory
        snippet_pattern = pattern_factory.create_expression(snippet, extra_declarations)
        results = match_pattern(code_pattern.children, [snippet_pattern])
        count: int = len(results)
        # plain assert_with_msg
        self.assertEqual(1, count, "count = " + str(count))


def test_it_can_be_created():
    it = PythonRstNode(ast.Pass())
    assert it


def test_it_has_elements():
    it = PythonRstNode(ast.parse("def fun():  pass"))
    assert it[0] == it.children[0]

import pytest

from hamcrest import assert_that, is_
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.syntax_tree.match_finder import is_match



class TestPythonAstMatcherBasic:
    """
    Test Class for basic match functionality.

    This test class documents how the AST parser of Python matches "code with code".

    The test class high-lights the representations of structure-bearing, composite AST nodes 
    as used by the AST parser.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_if_statements(self):
        code_if_then_statement = "if c1:\n    pass"
        code_if_then_else_statement = "if c1:\n    pass\nelse:   \n    pass"
        code_if_then_elif_statement = "if c1:\n    pass\nelif c2:\n    pass"
        code_if_then_else_if_statement = "if c1:\n    pass\nelse:\n    if c2:\n        pass"

        if_then_statement = self.pattern_factory.create_statement(code_if_then_statement)
        if_then_else_statement = self.pattern_factory.create_statement(code_if_then_else_statement)
        if_then_elif_statement = self.pattern_factory.create_statement(code_if_then_elif_statement)
        if_then_else_if_statement = self.pattern_factory.create_statement(code_if_then_else_if_statement)

        assert_that(is_match(if_then_statement, if_then_statement), is_(True))
        assert_that(is_match(if_then_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_statement, if_then_elif_statement), is_(False))
        assert_that(is_match(if_then_statement, if_then_else_if_statement), is_(False))

        assert_that(is_match(if_then_else_statement, if_then_statement), is_(False))
        assert_that(is_match(if_then_else_statement, if_then_else_statement), is_(True))
        assert_that(is_match(if_then_else_statement, if_then_elif_statement), is_(False))
        assert_that(is_match(if_then_else_statement, if_then_else_if_statement), is_(False))

        assert_that(is_match(if_then_elif_statement, if_then_statement), is_(False))
        assert_that(is_match(if_then_elif_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_elif_statement, if_then_elif_statement), is_(True))
        assert_that(is_match(if_then_elif_statement, if_then_else_if_statement), is_(True))

        assert_that(is_match(if_then_else_if_statement, if_then_statement), is_(False))
        assert_that(is_match(if_then_else_if_statement, if_then_else_statement), is_(False))
        assert_that(is_match(if_then_else_if_statement, if_then_elif_statement), is_(True))
        assert_that(is_match(if_then_else_if_statement, if_then_else_if_statement), is_(True))


if __name__ == "__main__":
    pytest.main()

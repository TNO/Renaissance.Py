import pytest

from hamcrest import assert_that, is_, is_not

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.match_finder import is_match, match_pattern


class TestPythonMatcherBasic:
    """
    Test Class for elementary match functionality.

    This test class documents how we want to match "code with code" in Python.

    The test class high-lights the insensitivity of code to comments and white spaces.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_statements_with_comment_and_whitespace(self):
        """
        How are statements with comments and whitespace handled by the parser?
        """
        statement = "x = 1"
        statement_with_comment = "x = 1  # This is a comment"
        statement_with_new_line = "x        =       1   "
        statement_with_whitespace = "x   =   1   "
        statement_with_comment_and_whitespace = "# This is a comment\nx    =    1   \n# This is a comment   "

        representations = [
            statement,
            statement_with_comment,
            statement_with_new_line,
            statement_with_whitespace,
            statement_with_comment_and_whitespace,
        ]
        expressions = map(self.pattern_factory.create_statement, representations)

        for expression1 in expressions:
            for expression2 in expressions:
                assert_that(expression1, is_(expression2))


if __name__ == "__main__":
    pytest.main()

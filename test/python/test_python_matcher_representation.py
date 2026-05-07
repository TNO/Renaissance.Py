import pytest
import ast

from hamcrest import assert_that, is_, is_not

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.match_finder import is_match, match_pattern


class TestPythonMatcherRepresentation:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_integer_representation(self):
        """
        How are the different integer representations handled by the parser?
        """
        normal = "1000"
        readable = "1_000"
        scientific_lower = "1e3"
        scientific_upper = "1E3"
        scientific_signed = "1E+3"
        binary_lower = "0b1111101000"
        binary_upper = "0B1111101000"
        octal_lower = "0o1750"
        octal_upper = "0O1750"
        hexadecimal_lower = "0x3e8"
        hexadecimal_upper = "0X3E8"

        representations = [
            normal,
            readable,
            scientific_lower,
            scientific_upper,
            scientific_signed,
            binary_lower,
            binary_upper,
            octal_lower,
            octal_upper,
            hexadecimal_lower,
            hexadecimal_upper,
        ]

        expressions = map(self.pattern_factory.create_expression, representations)

        for expression1 in expressions:
            for expression2 in expressions:
                assert_that(expression1, is_(expression2))

        signed = "+1000"
        expression_signed = self.pattern_factory.create_expression(signed)
        for expression in expressions:
            assert_that(expression_signed, is_not(expression))

    def test_character_representation(self):
        """
        How are the different character representations handled by the parser?
        """
        normal_single = "'1'"
        normal_double = '"1"'
        escape_octal_single = "'\\061'"
        escape_octal_double = '"\\061"'
        escape_hexadecimal_single = "'\\x31'"
        escape_hexadecimal_double = '"\\x31"'
        unicode_single = "'\\u0031'"
        unicode_double = '"\u0031"'

        representations = [
            normal_single,
            normal_double,
            escape_octal_single,
            escape_octal_double,
            escape_hexadecimal_single,
            escape_hexadecimal_double,
            unicode_single,
            unicode_double,
        ]

        expressions = map(self.pattern_factory.create_expression, representations)

        for expression1 in expressions:
            for expression2 in expressions:
                assert_that(is_match(expression1, expression2), is_(True))

    def test_string_representation(self):
        """
        How are the different string representations handled by the parser?
        """
        normal_single = "'abcdef'"
        normal_double = '"abcdef"'

        implicit_concatenated_single = "'abc' 'def'"
        implicit_concatenated_double = '"abc" "def"'

        representations = [
            normal_single,
            normal_double,
            implicit_concatenated_single,
            implicit_concatenated_double,
        ]

        expressions = map(self.pattern_factory.create_expression, representations)

        for expression1 in expressions:
            for expression2 in expressions:
                assert_that(is_match(expression1, expression2), is_(True))

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

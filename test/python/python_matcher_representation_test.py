import pytest
import ast

from hamcrest import assert_that, is_

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.match_finder import is_match, match_pattern


class TestPythonMatcherRepresentation:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_integer_representation(self):
        """
        This test case documents the semantic power of [the Python parser ast](https://docs.python.org/3/library/ast.html) 
        with respect to integer representations.

        In particular, different integer representations are not semantically relevant.
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
                assert_that(is_match(expression1, expression2), is_(True))

        signed = "+1000"
        expression_signed = self.pattern_factory.create_expression(signed)
        for expression in expressions:
            assert_that(is_match(expression_signed, expression), is_(False))

    def test_character_representation(self):
        """
        This test case documents the semantic power of [the Python parser ast](https://docs.python.org/3/library/ast.html) 
        with respect to character representations.

        In particular, different character representations are not semantically relevant.
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

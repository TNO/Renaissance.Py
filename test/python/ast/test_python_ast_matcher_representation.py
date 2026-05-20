import pytest

from hamcrest import assert_that, is_, is_not

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.match_finder import is_match, match_pattern


class TestPythonAstMatcherRepresentation:
    """
    Test Class for elementary match functionality.
    
    This test class documents how the AST parser of Python matches "symbols with symbols".

    The test class high-lights the representations of data-bearing, leave AST nodes
    as used by the AST parser.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_literal_whole_numbers_representation(self):
        """
        How are the different representations of literal instances of whole numbers handled by the parser?
        """
        normal = "1000"
        readable = "1_000"
        scientific_power_0 = "1000e0"
        scientific_POWER_0 = "1000E0"
        scientific_power_plus0 = "1000e+0"
        scientific_power_minus0 = "1000e-0"
        scientific_power_3 = "1e3"
        scientific3_POWER_3 = "1E3"
        scientific3_POWER_plus3 = "1E+3"
        scientific3_POWER_minus3 = "1000000E-3"
        binary_lower = "0b1111101000"
        binary_upper = "0B1111101000"
        octal_lower = "0o1750"
        octal_upper = "0O1750"
        hexadecimal_lower = "0x3e8"
        hexadecimal_upper = "0X3E8"
        float = "1000.000"

        representations = [
            normal,
            readable,
            scientific_power_0,
            scientific_POWER_0,
            scientific_power_plus0,
            scientific_power_minus0,
            scientific_power_3,
            scientific3_POWER_3,
            scientific3_POWER_plus3,
            scientific3_POWER_minus3,
            binary_lower,
            binary_upper,
            octal_lower,
            octal_upper,
            hexadecimal_lower,
            hexadecimal_upper,
            float,
        ]

        expressions = map(self.pattern_factory.create_expression, representations)

        for expression1 in expressions:
            for expression2 in expressions:
                assert_that(expression1, is_(expression2))

        signed = "+1000"
        expression_signed = self.pattern_factory.create_expression(signed)
        for expression in expressions:
            assert_that(expression_signed, is_not(expression))

    def test_literal_real_numbers_representation(self):
        """
        How are the different representations of literal instances of real numbers handled by the parser?
        """
        normal = "0.123456"
        more_significant_digits = "0.123456000"
        readable = "0.123_456"
        scientific_power_0 = "0.123456e0"
        scientific_power_plus0 = "0.123456e+0"
        scientific_power_minus0 = "0.123456e-0"
        scientific_power_minus3 = "123.456e-3"
        scientific_power_minus6 = "123456e-6"

        representations = [
            normal,
            more_significant_digits,
            readable,
            scientific_power_0,
            scientific_power_plus0,
            scientific_power_minus0,
            scientific_power_minus3,
            scientific_power_minus6,
        ]

        expressions = map(self.pattern_factory.create_expression, representations)

        for expression1 in expressions:
            for expression2 in expressions:
                assert_that(expression1, is_(expression2))

        fraction = "123456/1000000"
        expression_fraction = self.pattern_factory.create_expression(fraction)
        for expression in expressions:
            assert_that(expression_fraction, is_not(expression))

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
        unicode_double = '"\\u0031"'

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
                assert_that(expression1, is_(expression2))

    def test_string_representation(self):
        """
        How are the different string representations handled by the parser?
        """
        normal_single = "'abcdef'"
        normal_double = '"abcdef"'

        implicit_concatenated_single = "'abc' 'def'"
        implicit_concatenated_double = '"abc" "def"'
        implicit_concatenated_mixed = "\"abc\" 'def'"

        representations = [
            normal_single,
            normal_double,
            implicit_concatenated_single,
            implicit_concatenated_double,
            implicit_concatenated_mixed,
        ]

        expressions = map(self.pattern_factory.create_expression, representations)

        for expression1 in expressions:
            for expression2 in expressions:
                assert_that(expression1, is_(expression2))

        explicit_concatenated_single = "'abc' + 'def'"
        explicit_concatenated_double = '"abc" + "def"'
        explicit_concatenated_mixed = "\"abc\" + 'def'"

        explicit_concatenated_representations = [
            explicit_concatenated_single,
            explicit_concatenated_double,
            explicit_concatenated_mixed,
        ]

        expressions_explicit_concatenated = map(self.pattern_factory.create_expression, explicit_concatenated_representations)
        for expression1 in expressions_explicit_concatenated:
            for expression2 in expressions_explicit_concatenated:
                assert_that(expression1, is_(expression2))

        for expression_explicit_concatenated in expressions_explicit_concatenated:
            for expression in expressions:
                assert_that(expression_explicit_concatenated, is_not(expression))

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

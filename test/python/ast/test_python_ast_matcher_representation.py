import pytest

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory

from renaissance.syntax_tree.match_finder import AstProtocol

from utils.util_equivalence_classes import make_parametersets_of_equivalence_classes, assert_pair_equivalence


class TestPythonAstMatcherRepresentation:
    """
    Test Class for elementary match functionality.

    This test class documents how the AST parser of Python matches "symbols with symbols".

    The test class high-lights the representations of data-bearing, leave AST nodes
    as used by the AST parser.
    """

    WHOLE_NUMBER_REPRESENTATIONS: list[list[str]] = [
        # Base class: all represent the same whole number 1000
        [
            "1000",  # normal
            "1_000",  # readable
            "0b1111101000",  # binary lowercase
            "0B1111101000",  # binary uppercase
            "0o1750",  # octal lowercase
            "0O1750",  # octal uppercase
            "0x3e8",  # hexadecimal lowercase
            "0X3E8",  # hexadecimal uppercase
            "1000e0",  # scientific lowercase power 0
            "1000E0",  # scientific uppercase power 0
            "1000e+0",  # scientific lowercase power plus sign 0
            "1000e-0",  # scientific lowercase power minus sign 0
            "1e3",  # scientific lowercase power 3
            "1E3",  # scientific uppercase power 3
            "1E+3",  # scientific uppercase power plus sign 3
            "1000000E-3",  # scientific uppercase power minus sign 3
            "1000.000",  # float
        ],
        # Signed version
        [
            "+1000",
            "+1_000",
        ],
    ]

    REAL_NUMBER_REPRESENTATIONS: list[list[str]] = [
        # Base class: all represent the same real number 0.123456
        [
            "0.123456",  # normal
            "0.123456000",  # more significant digits / trailing zeros
            "0.123_456",  # readable (underscores)
            "0.123456e0",  # scientific power 0
            "0.123456e+0",  # scientific power +0
            "0.123456e-0",  # scientific power -0 (lexical variant)
            "123.456e-3",  # scientific power -3
            "123456e-6",  # scientific power -6
        ],
        # Fraction representation (expected NOT equivalent to the real literals)
        [
            "123456/1000000",
        ],
    ]

    CHARACTER_REPRESENTATIONS: list[list[str]] = [
        # Class 0: all represent the same character "1"
        [
            "'1'",  # normal single
            '"1"',  # normal double
            "'\\061'",  # octal escape single
            '"\\061"',  # octal escape double
            "'\\x31'",  # hex escape single
            '"\\x31"',  # hex escape double
            "'\\u0031'",  # unicode escape single
            '"\\u0031"',  # unicode escape double
        ],
        # Class 1: computed
        [
            "chr(49)",  # call producing "1"
            "chr(0x31)",  # same, different integer literal
        ],
    ]

    STRING_REPRESENTATIONS: list[list[str]] = [
        # Class 0: string literal forms that the parser treats as the same string value
        [
            "'abcdef'",  # normal single quotes
            '"abcdef"',  # normal double quotes
            "'abc' 'def'",  # implicit concatenation: single quotes
            '"abc" "def"',  # implicit concatenation: double quotes
            "\"abc\" 'def'",  # implicit concatenation: mixed quotes
        ],
        # Class 1: explicit concatenation (should be a different AST construction)
        [
            "'abc' + 'def'",  # explicit concatenation: single quotes
            '"abc" + "def"',  # explicit concatenation: double quotes
            "\"abc\" + 'def'",  # explicit concatenation: mixed quotes
        ],
        # Class 2:formatted strings
        [
            "f'{\"abcdef\"}'",  # formatted string single quotes
            "f\"{'abcdef'}\"",  # formatted string double quotes
        ],
    ]

    TUPLE_REPRESENTATIONS: list[list[str]] = [
        # Assign tuple value to single variable
        [
            "a = 0, 1",     # without brackets
            "a = 0, 1,",    # without brackets, with trailing comma
            "a = (0, 1)",   # with brackets
            "a = (0, 1,)",   # with brackets, with trailing comma
        ],
        # Assign tuple variable to two variables
        [
            "a, b = tuple",     # without brackets
            "a, b, = tuple",     # without brackets, with trailing comma
            "(a, b) = tuple",   # with brackets
            "(a, b) = tuple",   # with brackets, with trailing comma
        ],
        # Assign tuple value to two variables
        [
            "a, b = 0, 1",       # without brackets
            "a, b = 0, 1,",      # without brackets and with trailing comma for value
            "a, b = (0, 1)",     # with bracket for value
            "a, b = (0, 1,)",    # with bracket and trailing comma for value

            "a, b, = 0, 1",      # without brackets, with trailing comma for variables
            "a, b, = 0, 1,",     # without brackets, with trailing commas
            "a, b, = (0, 1)",    # with bracket for value, with trailing comma for variables
            "a, b, = (0, 1,)",    # with bracket for value, with trailing commas

            "(a, b) = 0, 1",     # with bracket for variables
            "(a, b) = 0, 1,",    # with bracket for variables, with trailing comma for value
            "(a, b) = (0, 1)",   # with brackets
            "(a, b) = (0, 1,)",  # with brackets, with trailing comma for value
            
            "(a, b,) = 0, 1",      # with brackets and trailing comma for variables
            "(a, b,) = 0, 1,",     # with brackets for variables and with trailing commas
            "(a, b,) = (0, 1)",    # with brackets, with trailing comma for variables
            "(a, b,) = (0, 1,)",   # with brackets, with trailing commas
        ],
        
    ]

    # generate test cases from equivalence classes
    PATTERN_FACTORY = PythonPatternFactory(PythonFactory(PythonRstNode))

    @pytest.mark.parametrize(
        "a, b, expected",
        make_parametersets_of_equivalence_classes("whole number", PATTERN_FACTORY.create_expression, WHOLE_NUMBER_REPRESENTATIONS)
        + make_parametersets_of_equivalence_classes("real number", PATTERN_FACTORY.create_expression, REAL_NUMBER_REPRESENTATIONS)
        + make_parametersets_of_equivalence_classes("character", PATTERN_FACTORY.create_expression, CHARACTER_REPRESENTATIONS)
        + make_parametersets_of_equivalence_classes("string", PATTERN_FACTORY.create_expression, STRING_REPRESENTATIONS)
        + make_parametersets_of_equivalence_classes("string", PATTERN_FACTORY.create_statement, TUPLE_REPRESENTATIONS)
    )
    def test_pairs_of_equivalence_classes(self, a: AstProtocol, b: AstProtocol, expected: bool):
        assert_pair_equivalence(a, b, expected)


if __name__ == "__main__":
    pytest.main()

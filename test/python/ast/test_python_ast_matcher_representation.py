import pytest

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory

from utils.util_equivalence_classes import make_parametersets_of_equivalence_classes, assert_pair_equivalence


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

    WHOLE_NUMBER_PAIR_PARAMS = make_parametersets_of_equivalence_classes(WHOLE_NUMBER_REPRESENTATIONS)

    @pytest.mark.parametrize(
        "a_txt, b_txt, expected",
        WHOLE_NUMBER_PAIR_PARAMS,
    )
    def test_literal_whole_numbers_representation(self, a_txt: str, b_txt: str, expected: bool):
        """
        How are the different whole number representations handled by the parser?
        """
        assert_pair_equivalence(self.pattern_factory.create_expression, a_txt, b_txt, expected)

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

    REAL_NUMBER_PAIR_PARAMS = make_parametersets_of_equivalence_classes(REAL_NUMBER_REPRESENTATIONS)

    @pytest.mark.parametrize(
        "a_txt, b_txt, expected",
        REAL_NUMBER_PAIR_PARAMS,
    )
    def test_literal_real_numbers_representation(self, a_txt: str, b_txt: str, expected: bool):
        """
        How are the different real number representations handled by the parser?
        """
        assert_pair_equivalence(self.pattern_factory.create_expression, a_txt, b_txt, expected)

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

    CHARACTER_PAIR_PARAMS = make_parametersets_of_equivalence_classes(CHARACTER_REPRESENTATIONS)

    @pytest.mark.parametrize(
        "a_txt, b_txt, expected",
        CHARACTER_PAIR_PARAMS,
    )
    def test_character_representation(self, a_txt: str, b_txt: str, expected: bool):
        """
        How are the different character representations handled by the parser?
        """
        assert_pair_equivalence(self.pattern_factory.create_expression, a_txt, b_txt, expected)

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

    STRING_PAIR_PARAMS = make_parametersets_of_equivalence_classes(STRING_REPRESENTATIONS)

    @pytest.mark.parametrize(
        "a_txt, b_txt, expected",
        STRING_PAIR_PARAMS,
    )
    def test_string_representation(self, a_txt: str, b_txt: str, expected: bool):
        """
        How are the different string representations handled by the parser?
        """
        assert_pair_equivalence(self.pattern_factory.create_expression, a_txt, b_txt, expected)


if __name__ == "__main__":
    pytest.main()

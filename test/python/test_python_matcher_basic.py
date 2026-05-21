import pytest

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory

from utils.util_equivalence_classes import make_parametersets_of_equivalence_classes, assert_pair_equivalence


class TestPythonMatcherBasic:
    """
    Test Class for basic match functionality.

    This test class documents how we want to match "code with code" in Python.

    The test class high-lights the insensitivity of code to comments and white spaces.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    TRIVIA_CLASSES: list[list[str]] = [
        [
            "x = 1",
            "x = 1  # This is a comment",  # with comment
            "x  =  1  ",  # with extra spaces
            "x\t=\t1\t",  # with tabs
            "# This is a comment\nx    =    1   \n# This is a comment   ",  # multi line - mixed
        ],
        [
            "if c: pass\npass",
            "if c:\n    pass\npass",
        ],
        [
            "if c: pass;pass",      # with semicolon as statement separator
            "if c:\n    pass\n    pass",
        ],
    ]

    TRIVIA_PAIR_PARAMS = make_parametersets_of_equivalence_classes(TRIVIA_CLASSES)

    @pytest.mark.parametrize(
        "a_txt, b_txt, expected",
        TRIVIA_PAIR_PARAMS,
    )
    def test_trivia(self, a_txt: str, b_txt: str, expected: bool):
        """
        How are statements with comments and whitespaces handled by the parser?
        """
        assert_pair_equivalence(self.pattern_factory.create_statement, a_txt, b_txt, expected)


if __name__ == "__main__":
    pytest.main()

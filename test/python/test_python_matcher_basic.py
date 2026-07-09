from typing import Sequence

import pytest

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory

from renaissance.syntax_tree.match_finder import AstProtocol

from utils.util_equivalence_classes import make_parametersets_of_equivalence_classes, assert_pair_equivalence


class TestPythonMatcherBasic:
    """
    Test Class for basic match functionality.

    This test class documents how we want to match "code with code" in Python.

    The test class high-lights the insensitivity of code to comments and white spaces.
    """

    TRIVIA_CLASSES: list[list[str]] = [
        [
            "x = 1",
            "x = 1  # This is a comment",  # with comment
            "x  =  1  ",  # with extra spaces
            "x\t=\t1\t",  # with tabs
            "# This is a comment\nx    =    1   \n# This is a comment   ",  # multi line - mixed
        #    " x = 1",  # start with extra space
        ],
        # single if statement containing multiple statements
        [
            "if c: pass;pass",      # with semicolon as statement separator
            "if c:\n    pass\n    pass",
        ],
        # multiple statements, first statement is if statement 
        [
            "if c: pass\npass",
            "if c:\n    pass\npass",
        ],    
        ]

    # generate test cases from equivalence classes
    PATTERN_FACTORY = PythonPatternFactory(PythonFactory(PythonRstNode))

    # a and b have the same type as the return type of PATTERN_FACTORY.create_statements, 
    # which is Sequence[AstProtocol]
    @pytest.mark.parametrize(
        "a, b, expected", make_parametersets_of_equivalence_classes("trivia", PATTERN_FACTORY.create_statements, TRIVIA_CLASSES)
    )
    def test_pairs_of_equivalence_classes(self, a: Sequence[AstProtocol], b: Sequence[AstProtocol], expected: bool):
        assert_pair_equivalence(a, b, expected)

  
if __name__ == "__main__":
    pytest.main()

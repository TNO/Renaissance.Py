import pytest

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.syntax_tree.match_finder import AstProtocol
from utils.util_equivalence_classes import assert_pair_equivalence, make_parametersets_of_equivalence_classes


class TestPythonAstMatcherBasic:
    """Test Class for basic match functionality.

    This test class documents how the AST parser of Python matches "code with code".

    The test class high-lights the representations of structure-bearing, composite AST nodes
    as used by the AST parser.
    """

    IF_CLASSES: list[list[str]] = [
        [
            "if c1:\n    pass",  # if then statement
        ],
        [
            "if c1:\n    pass\nelse:   \n    pass",  # if then else statement
        ],
        [
            "if c1:\n    pass\nelif c2:\n    pass",  # if then elif statement
            "if c1:\n    pass\nelse:\n    if c2:\n        pass",  # if then else if statement
        ],
    ]

    # generate test cases from equivalence classes
    PATTERN_FACTORY = PythonPatternFactory(PythonFactory(PythonRstNode))

    # a and b have the same type as the return type of PATTERN_FACTORY.create_statement,
    # which is AstProtocol
    @pytest.mark.parametrize(
        "a, b, expected",
        make_parametersets_of_equivalence_classes("if statement", PATTERN_FACTORY.create_statement, IF_CLASSES),
    )
    def test_pairs_of_equivalence_classes(self, a: AstProtocol, b: AstProtocol, expected: bool):
        assert_pair_equivalence(a, b, expected)


if __name__ == "__main__":
    pytest.main()

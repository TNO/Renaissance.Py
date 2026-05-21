import pytest

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory

from utils.util_equivalence_classes import make_parametersets_of_equivalence_classes, assert_pair_equivalence


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

    IF_PAIR_PARAMS = make_parametersets_of_equivalence_classes(IF_CLASSES)

    @pytest.mark.parametrize(
        "a_txt, b_txt, expected",
        IF_PAIR_PARAMS,
    )
    def test_if_statements(self, a_txt: str, b_txt: str, expected: bool):
        """
        How are the different if statements handled by the parser?
        """
        assert_pair_equivalence(self.pattern_factory.create_statement, a_txt, b_txt, expected)


if __name__ == "__main__":
    pytest.main()

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests documenting basic code-to-code matching for the Python AST parser."""

from typing import ClassVar

import pytest

from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree.node_protocol import NodeProtocol
from utils.util_equivalence_classes import assert_pair_equivalence, make_parametersets_of_equivalence_classes


class TestPythonAstMatcherBasic:
    """Test Class for basic match functionality.

    This test class documents how the AST parser of Python matches "code with code".

    The test class high-lights the representations of structure-bearing, composite AST nodes
    as used by the AST parser.
    """

    IF_CLASSES: ClassVar[list[list[str]]] = [
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

    TYPEHINT_CLASSES: ClassVar[list[list[str]]] = [
        # type hints comments are ignored
        # as False is the default value of type_comments in the [ast.parse](https://docs.python.org/3/library/ast.html#ast.parse) function.
        [
            "x = 0",  # Assign - no type hint
            "x = 0 # type: ignore",  # Assign - with ignore type hint in comment
            "x = 0 # type: int",  # Assign - with type hint `int` in comment
        ],
        [
            "x: int = 0",  # AnnAssign - with type hint `int`
        ],
    ]

    # generate test cases from equivalence classes
    PATTERN_FACTORY: ClassVar[PythonPatternFactory] = PythonPatternFactory(PythonFactory(PythonRstNode))

    # a and b have the same type as the return type of PATTERN_FACTORY.create_statement,
    # which is NodeProtocol
    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        make_parametersets_of_equivalence_classes("if statement", PATTERN_FACTORY.create_statement, IF_CLASSES)
        + make_parametersets_of_equivalence_classes("type hint", PATTERN_FACTORY.create_statement, TYPEHINT_CLASSES),
    )
    def test_pairs_of_equivalence_classes(self, a: NodeProtocol, b: NodeProtocol, *, expected: bool) -> None:
        """AI: Verify if-statement pairs from the same or different equivalence classes match as expected."""
        assert_pair_equivalence(a, b, expected)


if __name__ == "__main__":
    pytest.main()

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

    # ast.If has three fields: test, body and orelse.
    # `elif` is an If that is the only statement in orelse; a missing `else` is an empty orelse.
    IF_CLASSES: ClassVar[list[list[str]]] = [
        # brackets, single-line form, layout and comments are not in the AST
        [
            "if c1:\n    pass",
            "if c1: pass",
            "if (c1):\n    pass",
            "if c1:\n    # comment\n    pass",
        ],
        # `else: pass` is not the same as no `else`
        [
            "if c1:\n    pass\nelse:   \n    pass",
        ],
        # elif is sugar for else with a single nested if
        [
            "if c1:\n    pass\nelif c2:\n    pass",
            "if c1:\n    pass\nelse:\n    if c2:\n        pass",
        ],
        [
            "if c1:\n    pass\nelif c2:\n    pass\nelse:\n    pass",
            "if c1:\n    pass\nelse:\n    if c2:\n        pass\n    else:\n        pass",
        ],
        # the parser does not rewrite logic
        [
            "if c1 and c2:\n    pass",
        ],
        [
            "if c1:\n    if c2:\n        pass",
        ],
        [
            "if c1:\n    a\nelse:\n    b",
        ],
        [
            "if not c1:\n    b\nelse:\n    a",
        ],
    ]

    # Assign has targets, value and type_comment; AnnAssign has target, annotation, value and simple.
    # The binding parses with type_comments=False (the default of [ast.parse](https://docs.python.org/3/library/ast.html#ast.parse)),
    # so type comments are dropped like other comments.
    TYPEHINT_CLASSES: ClassVar[list[list[str]]] = [
        # comments, including type comments, are not in the AST
        [
            "x = 0",
            "x = 0 # type: ignore",
            "x = 0 # type: int",
        ],
        # an annotation makes it an AnnAssign
        [
            "x: int = 0",
        ],
        # brackets around the target set simple=0, see [ast.AnnAssign](https://docs.python.org/3/library/ast.html#ast.AnnAssign)
        [
            "(x): int = 0",
        ],
        # a string annotation is a Constant, not a Name
        [
            "x: 'int' = 0",
        ],
        # an annotation without a value has value=None
        [
            "x: int",
        ],
    ]

    # ast.Call has three fields: func, args and keywords.
    # `*x` is a Starred node in args; `**x` is a keyword with arg=None in keywords.
    # Order within each list is kept; how args and keywords interleave in the source is lost,
    # which matches the language: `*x` after keyword arguments is still evaluated before them.
    # See [Calls](https://docs.python.org/3/reference/expressions.html#calls).
    # Each function name (f, g, h, ...) is one topic; pairs across topics differ only in func.
    FUNCTIONCALL_CLASSES: ClassVar[list[list[str]]] = [
        # brackets, a trailing comma and layout are not in the AST
        [
            "f(a)",
            "f(a,)",
            "(f)(a)",
            "f((a))",
        ],
        # keyword order is kept
        [
            "g(a=1, b=2)",
        ],
        [
            "g(b=2, a=1)",
        ],
        # only the interleaving of args and keywords differs
        [
            "h(a, *b, *c, k=1, **y, z=2)",
            "h(a, *b, k=1, *c, **y, z=2)",
            "h(a, k=1, *b, *c, **y, z=2)",
        ],
        # order of unpacking in args is kept
        [
            "i(*a, *b)",
        ],
        [
            "i(*b, *a)",
        ],
        # the parser does not unpack literals
        [
            "j(a,b)",
        ],
        [
            "j(*[a,b])",
        ],
        [
            "j(*(a,b))",
        ],
        # `**d` is a keyword too, so its position among the keywords is kept
        [
            "k(a=1, **d)",
        ],
        [
            "k(**d, a=1)",
        ],
        # keywords passed through a mapping are not k=v keywords
        [
            "m(k=v)",
        ],
        [
            "m(**{'k': v})",
        ],
        [
            "m(**dict(k=v))",
        ],
    ]

    # generate test cases from equivalence classes
    PATTERN_FACTORY: ClassVar[PythonPatternFactory] = PythonPatternFactory(PythonFactory(PythonRstNode))

    # a and b have the same type as the return type of PATTERN_FACTORY.create_statement,
    # which is NodeProtocol
    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        make_parametersets_of_equivalence_classes("if statement", PATTERN_FACTORY.create_statement, IF_CLASSES)
        + make_parametersets_of_equivalence_classes("type hint", PATTERN_FACTORY.create_statement, TYPEHINT_CLASSES)
        + make_parametersets_of_equivalence_classes("function call", PATTERN_FACTORY.create_expression, FUNCTIONCALL_CLASSES),
    )
    def test_pairs_of_equivalence_classes(self, a: NodeProtocol, b: NodeProtocol, *, expected: bool) -> None:
        """AI: Verify if-statement pairs from the same or different equivalence classes match as expected."""
        assert_pair_equivalence(a, b, expected)


if __name__ == "__main__":
    pytest.main()

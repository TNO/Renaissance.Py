# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the AST navigation helpers in ast_utils."""

from collections.abc import Callable

import pytest
from hamcrest import assert_that, equal_to

from renaissance.integrations.clang import ClangASTNode
from renaissance.utils.ast_utils import is_ancestor_of

# Two functions with the same body, so their nodes are structurally equal.
SOURCE = "void f() { int x = 0; }\nvoid g() { int x = 0; }\n"


def _root(root: ClangASTNode) -> ClangASTNode:
    """Return the translation unit."""
    return root


def _first_function(root: ClangASTNode) -> ClangASTNode:
    """Return the definition of f."""
    return root.children[-2]


def _second_function(root: ClangASTNode) -> ClangASTNode:
    """Return the definition of g."""
    return root.children[-1]


def _statement_of_first(root: ClangASTNode) -> ClangASTNode:
    """Return the declaration statement in the body of f."""
    return _first_function(root).children[-1].children[-1]


def _statement_of_second(root: ClangASTNode) -> ClangASTNode:
    """Return the declaration statement in the body of g."""
    return _second_function(root).children[-1].children[-1]


class TestIsAncestorOf:
    """Tests for is_ancestor_of."""

    @pytest.mark.parametrize(
        ("ancestor", "node", "expected"),
        [
            (_root, _statement_of_first, True),
            (_first_function, _statement_of_first, True),
            (_first_function, _first_function, False),
            (_statement_of_first, _first_function, False),
            (_first_function, _statement_of_second, False),
            (_second_function, _statement_of_first, False),
        ],
    )
    def test_is_ancestor_of(
        self,
        ancestor: Callable[[ClangASTNode], ClangASTNode],
        node: Callable[[ClangASTNode], ClangASTNode],
        expected: bool,  # noqa: FBT001
    ) -> None:
        """Verify is_ancestor_of follows parent links and tells structurally equal nodes apart."""
        root = ClangASTNode.load_from_text(SOURCE, "test.c")
        assert_that(_first_function(root), equal_to(_second_function(root)), "f and g must be structurally equal")
        assert_that(is_ancestor_of(ancestor(root), node(root)), equal_to(expected))

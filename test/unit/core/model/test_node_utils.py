# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the sibling lookup of the core model."""

from hamcrest import assert_that, none, same_instance

from renaissance.core.model import next_sibling, preceding_sibling
from renaissance.integrations.clang import ClangASTNode

# Two functions with the same body, so their nodes are structurally equal.
SOURCE = "void f() { int x = 0; }\nvoid g() { int x = 0; }\n"


def _first_function(root: ClangASTNode) -> ClangASTNode:
    """Return the definition of f."""
    return root.children[-2]


def _second_function(root: ClangASTNode) -> ClangASTNode:
    """Return the definition of g."""
    return root.children[-1]


class TestSiblings:
    """Tests for preceding_sibling and next_sibling with structurally equal siblings."""

    def test_preceding_sibling_of_second_is_first(self) -> None:
        """Verify preceding_sibling does not stop at an earlier sibling that is structurally equal."""
        root = ClangASTNode.load_from_text(SOURCE, "test.c")
        assert_that(preceding_sibling(_second_function(root)), same_instance(_first_function(root)))

    def test_next_sibling_of_first_is_second(self) -> None:
        """Verify next_sibling returns the following node."""
        root = ClangASTNode.load_from_text(SOURCE, "test.c")
        assert_that(next_sibling(_first_function(root)), same_instance(_second_function(root)))

    def test_next_sibling_of_last_is_none(self) -> None:
        """Verify next_sibling of the last node is None, not the node itself."""
        root = ClangASTNode.load_from_text(SOURCE, "test.c")
        assert_that(next_sibling(_second_function(root)), none())

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the navigation of a syntax tree: the ancestors and the siblings of a node."""

from collections.abc import Callable

import pytest
from hamcrest import assert_that, contains_exactly, equal_to, is_, none, same_instance

from renaissance.core.navigate import (
    ancestors,
    is_ancestor_of,
    is_proper_ancestor_of,
    nearest_ancestor,
    nearest_proper_ancestor,
    next_sibling,
    previous_sibling,
    proper_ancestors,
)


class Node:
    """A test double of a node, with structural equality as the nodes of the parser bindings have."""

    def __init__(self, kind: str, *children: "Node") -> None:
        """Create a node of kind with children, and make it their parent."""
        self.kind = kind
        self.parent: Node | None = None
        self.children: list[Node] = list(children)
        for child in children:
            child.parent = self

    def __eq__(self, other: object) -> bool:
        """Compare by kind and children, not by identity."""
        return isinstance(other, Node) and self.kind == other.kind and self.children == other.children

    def __hash__(self) -> int:
        """Hash consistently with __eq__."""
        return hash(self.kind)

    def __repr__(self) -> str:
        """Show the kind."""
        return f"Node({self.kind!r})"


class Tree:
    """A module with two structurally equal functions f and g, each with one statement."""

    def __init__(self) -> None:
        """Build the tree."""
        self.root = Node("module", Node("function", Node("statement")), Node("function", Node("statement")))
        self.f, self.g = self.root.children
        self.statement_of_f = self.f.children[0]
        self.statement_of_g = self.g.children[0]


def with_kind(kind: str) -> Callable[[Node], bool]:
    """Return a predicate that is true for the nodes of kind."""
    return lambda node: node.kind == kind


@pytest.fixture
def tree() -> Tree:
    """Return a fresh tree."""
    return Tree()


class TestAncestors:
    """Tests for is_ancestor_of, is_proper_ancestor_of, ancestors and proper_ancestors."""

    def test_node_is_its_own_ancestor_but_not_its_own_proper_ancestor(self, tree: Tree) -> None:
        """Verify an ancestor includes the node itself, and a proper ancestor excludes it."""
        assert_that(is_ancestor_of(tree.f, tree.f), is_(True))
        assert_that(is_proper_ancestor_of(tree.f, tree.f), is_(False))

    def test_parent_and_root_are_proper_ancestors(self, tree: Tree) -> None:
        """Verify the parent and the root are proper ancestors of a statement."""
        assert_that(is_proper_ancestor_of(tree.f, tree.statement_of_f), is_(True))
        assert_that(is_proper_ancestor_of(tree.root, tree.statement_of_f), is_(True))
        assert_that(is_ancestor_of(tree.root, tree.statement_of_f), is_(True))

    def test_descendant_is_not_an_ancestor(self, tree: Tree) -> None:
        """Verify a statement is not an ancestor of its function."""
        assert_that(is_ancestor_of(tree.statement_of_f, tree.f), is_(False))

    def test_structurally_equal_nodes_are_told_apart(self, tree: Tree) -> None:
        """Verify neither of two structurally equal functions is an ancestor of the other or of its statement."""
        assert_that(tree.f, equal_to(tree.g), "precondition: f and g are structurally equal")
        assert_that(tree.statement_of_f, equal_to(tree.statement_of_g), "precondition: their statements are structurally equal")
        assert_that(is_ancestor_of(tree.f, tree.g), is_(False))
        assert_that(is_ancestor_of(tree.g, tree.f), is_(False))
        assert_that(is_ancestor_of(tree.f, tree.statement_of_g), is_(False))
        assert_that(is_ancestor_of(tree.g, tree.statement_of_f), is_(False))

    def test_ancestors_start_with_the_node_itself(self, tree: Tree) -> None:
        """Verify ancestors returns the node, then its parent, up to the root."""
        assert_that(
            ancestors(tree.statement_of_g),
            contains_exactly(same_instance(tree.statement_of_g), same_instance(tree.g), same_instance(tree.root)),
        )

    def test_proper_ancestors_start_with_the_parent(self, tree: Tree) -> None:
        """Verify proper_ancestors returns the parent, up to the root."""
        assert_that(proper_ancestors(tree.statement_of_g), contains_exactly(same_instance(tree.g), same_instance(tree.root)))

    def test_root_is_its_only_ancestor(self, tree: Tree) -> None:
        """Verify the root has no parent, so it is its only ancestor."""
        assert_that(tree.root.parent, none())
        assert_that(ancestors(tree.root), contains_exactly(same_instance(tree.root)))
        assert_that(proper_ancestors(tree.root), contains_exactly())


class TestNearestAncestor:
    """Tests for nearest_ancestor and nearest_proper_ancestor."""

    def test_nearest_ancestor_can_be_the_node_itself(self, tree: Tree) -> None:
        """Verify nearest_ancestor returns the node itself when the predicate holds for it."""
        assert_that(nearest_ancestor(tree.f, with_kind("function")), same_instance(tree.f))

    def test_nearest_proper_ancestor_is_never_the_node_itself(self, tree: Tree) -> None:
        """Verify nearest_proper_ancestor skips the node itself."""
        assert_that(nearest_proper_ancestor(tree.f, with_kind("function")), none())

    def test_nearest_match_not_a_farther_one(self) -> None:
        """Verify the nearest matching ancestor is returned, not a farther one."""
        statement = Node("statement")
        inner = Node("function", statement)
        Node("function", inner)
        assert_that(nearest_ancestor(statement, with_kind("function")), same_instance(inner))
        assert_that(nearest_proper_ancestor(statement, with_kind("function")), same_instance(inner))

    def test_no_match_is_none(self, tree: Tree) -> None:
        """Verify None is returned when nothing matches, including at the root."""
        assert_that(nearest_ancestor(tree.statement_of_f, with_kind("class")), none())
        assert_that(nearest_proper_ancestor(tree.statement_of_f, with_kind("class")), none())
        assert_that(nearest_ancestor(tree.root, with_kind("function")), none())
        assert_that(nearest_proper_ancestor(tree.root, with_kind("module")), none())


class TestSiblings:
    """Tests for next_sibling and previous_sibling."""

    def test_previous_sibling_of_second_is_first(self, tree: Tree) -> None:
        """Verify previous_sibling does not stop at an earlier sibling that is structurally equal."""
        assert_that(tree.f, equal_to(tree.g), "precondition: f and g are structurally equal")
        assert_that(previous_sibling(tree.g), same_instance(tree.f))

    def test_next_sibling_of_first_is_second(self, tree: Tree) -> None:
        """Verify next_sibling finds the node by identity, not at a structurally equal sibling."""
        assert_that(tree.f, equal_to(tree.g), "precondition: f and g are structurally equal")
        assert_that(next_sibling(tree.f), same_instance(tree.g))

    def test_first_child_has_no_previous_sibling(self, tree: Tree) -> None:
        """Verify previous_sibling of the first child is None."""
        assert_that(previous_sibling(tree.f), none())

    def test_last_child_has_no_next_sibling(self, tree: Tree) -> None:
        """Verify next_sibling of the last child is None, not the node itself."""
        assert_that(next_sibling(tree.g), none())

    def test_root_has_no_siblings(self, tree: Tree) -> None:
        """Verify the root has neither a previous nor a next sibling."""
        assert_that(previous_sibling(tree.root), none())
        assert_that(next_sibling(tree.root), none())

    def test_node_missing_from_its_parent_is_an_error(self) -> None:
        """Verify a node that is not among the children of its parent raises ValueError."""
        orphan = Node("statement")
        orphan.parent = Node("function")
        with pytest.raises(ValueError, match="not among the children"):
            next_sibling(orphan)

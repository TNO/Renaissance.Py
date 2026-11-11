# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The navigation of a syntax tree: the ancestors and the siblings of a node.

Nodes are compared by identity, never by equality: node equality is structural, so two nodes at different places in the
tree can be equal.
"""

from collections.abc import Callable, Iterator, Sequence

from renaissance.core.navigate.protocols import HasParent, NodeNavigateProtocol


def _iterate_proper_ancestors[NodeT: HasParent](node: NodeT) -> Iterator[NodeT]:
    current = node.parent
    while current is not None:
        yield current
        current = current.parent


def is_ancestor_of[NodeT: HasParent](ancestor: NodeT, node: NodeT) -> bool:
    """Return whether ancestor is node itself or a proper ancestor of node."""
    return ancestor is node or is_proper_ancestor_of(ancestor, node)


def is_proper_ancestor_of[NodeT: HasParent](ancestor: NodeT, node: NodeT) -> bool:
    """Return whether ancestor is an ancestor of node other than node itself."""
    return any(candidate is ancestor for candidate in _iterate_proper_ancestors(node))


def ancestors[NodeT: HasParent](node: NodeT) -> Sequence[NodeT]:
    """Return node, its parent, and so on up to the root."""
    return [node, *_iterate_proper_ancestors(node)]


def proper_ancestors[NodeT: HasParent](node: NodeT) -> Sequence[NodeT]:
    """Return the parent of node, its parent, and so on up to the root."""
    return list(_iterate_proper_ancestors(node))


def nearest_ancestor[NodeT: HasParent](node: NodeT, predicate: Callable[[NodeT], bool]) -> NodeT | None:
    """Return the first of the ancestors of node for which predicate is true, or None. This can be node itself."""
    return node if predicate(node) else nearest_proper_ancestor(node, predicate)


def nearest_proper_ancestor[NodeT: HasParent](node: NodeT, predicate: Callable[[NodeT], bool]) -> NodeT | None:
    """Return the first of the proper ancestors of node for which predicate is true, or None. This is never node itself."""
    return next((ancestor for ancestor in _iterate_proper_ancestors(node) if predicate(ancestor)), None)


def _sibling_at[NodeT: NodeNavigateProtocol](node: NodeT, offset: int) -> NodeT | None:
    parent = node.parent
    if parent is None:
        return None
    siblings = parent.children
    for index, sibling in enumerate(siblings):
        if sibling is node:
            target = index + offset
            return siblings[target] if 0 <= target < len(siblings) else None
    msg = "node is not among the children of its parent"
    raise ValueError(msg)


def next_sibling[NodeT: NodeNavigateProtocol](node: NodeT) -> NodeT | None:
    """Return the sibling directly after node, or None.

    Goes up to the parent, down to its children, and takes the position after node in that sequence.
    """
    return _sibling_at(node, 1)


def previous_sibling[NodeT: NodeNavigateProtocol](node: NodeT) -> NodeT | None:
    """Return the sibling directly before node, or None.

    Goes up to the parent, down to its children, and takes the position before node in that sequence.
    """
    return _sibling_at(node, -1)

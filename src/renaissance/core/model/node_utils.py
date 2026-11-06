# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Generic node helpers: traversal, sibling lookup, and the display setting for node kinds."""

from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

# TODO(FrancescoPezzella): Replace with a lazy import in Python 3.15.
#  https://github.com/TNO/Renaissance.Py/issues/275
if TYPE_CHECKING:
    from renaissance.core.model.node_protocol import NodeProtocol

DISPLAY_PARSER_KIND: ContextVar[bool] = ContextVar("display_parser_kind", default=False)


@contextmanager
def display_context(display_parser_kind: bool):
    """AI: Temporarily set whether node display uses parser kind instead of semantic kind."""
    token = DISPLAY_PARSER_KIND.set(display_parser_kind)
    try:
        yield
    finally:
        DISPLAY_PARSER_KIND.reset(token)


# duplicate of ast node process
def traverse(node):
    """AI: Yield node and all its descendants in breadth-first order."""
    todo = deque([node])
    while todo:
        node = todo.popleft()
        if hasattr(node, "children"):
            todo.extend(node.children)
        yield node


def process_node(node, action) -> None:
    """AI: Recursively apply action to node and all its descendants."""
    action(node)
    if node.children:
        for child in node.children:
            process_node(child, action)


def _sibling_at[NodeT: NodeProtocol](node: NodeT, offset: int) -> NodeT | None:
    """Return the sibling offset positions away from node in its parent's children, or None.

    The node is located by identity, since node equality is structural.
    """
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


def preceding_sibling[NodeT: NodeProtocol](node: NodeT) -> NodeT | None:
    """AI: Return the sibling immediately before node in its parent's children, or None."""
    return _sibling_at(node, -1)


def next_sibling[NodeT: NodeProtocol](node: NodeT) -> NodeT | None:
    """AI: Return the sibling immediately after node in its parent's children, or None."""
    return _sibling_at(node, 1)

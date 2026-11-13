# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Generic node helpers: traversal, and the display setting for node kinds."""

from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar

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

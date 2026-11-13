# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The navigation protocols.

When a parser binding lets the nodes of its AST provide one of these protocols, the functions of renaissance.core.navigate
that need it become available for these nodes.
"""

from collections.abc import Sequence
from typing import Protocol, Self


class HasParent(Protocol):
    """A node that provides its parent, so it can be navigated up the tree, to its ancestors."""

    # Read-only members keep the protocol covariant, so implementations may expose them as properties.
    @property
    def parent(self) -> Self | None:
        """Enclosing node, or None at the root."""
        ...


class HasChildren(Protocol):
    """A node that provides its children, so it can be navigated down the tree."""

    @property
    def children(self) -> Sequence[Self]:
        """Direct child nodes, in source order: the position in this sequence orders the siblings."""
        ...


class NodeNavigateProtocol(HasParent, HasChildren, Protocol):
    """A node that provides its parent and its children, so it can be navigated up and down the tree."""

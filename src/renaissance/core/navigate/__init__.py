# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The navigation of a syntax tree: the navigation protocols, and the ancestors and siblings of a node."""

from renaissance.core.navigate.navigate import (
    ancestors,
    is_ancestor_of,
    is_proper_ancestor_of,
    nearest_ancestor,
    nearest_proper_ancestor,
    next_sibling,
    previous_sibling,
    proper_ancestors,
)
from renaissance.core.navigate.protocols import HasChildren, HasParent, NodeNavigateProtocol

__all__ = [
    "HasChildren",
    "HasParent",
    "NodeNavigateProtocol",
    "ancestors",
    "is_ancestor_of",
    "is_proper_ancestor_of",
    "nearest_ancestor",
    "nearest_proper_ancestor",
    "next_sibling",
    "previous_sibling",
    "proper_ancestors",
]

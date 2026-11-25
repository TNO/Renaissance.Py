# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Structural protocol describing the interface consumed by generic syntax-tree algorithms."""

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from renaissance.core.model.semantic_kind import SemanticKind
from renaissance.core.navigate import NodeNavigateProtocol


@runtime_checkable
class NodeProtocol(NodeNavigateProtocol, Protocol):
    """Structural interface consumed by generic syntax-tree algorithms."""

    # Read-only members keep the protocol covariant, so implementations may expose them as properties.
    @property
    def parser_kind(self) -> str:
        """Node kind as reported by the underlying parser."""
        ...

    @property
    def semantic_kind(self) -> SemanticKind:
        """Language-independent classification of this node."""
        ...

    @property
    def properties(self) -> Mapping[str, Any]:
        """Parser-supplied attributes of this node."""
        ...

    @property
    def signature(self) -> str:
        """Source text of this node."""
        ...

    @property
    def name(self) -> str:
        """Declared name of this node, or an empty string if it has none."""
        ...

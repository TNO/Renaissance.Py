"""AI: Structural protocol describing the interface consumed by generic syntax-tree algorithms."""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, Self, runtime_checkable

from .semantic_kind import SemanticKind


@runtime_checkable
class NodeProtocol(Protocol):
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
    def children(self) -> Sequence[Self]:
        """Direct child nodes, in source order."""
        ...

    @property
    def signature(self) -> str:
        """Source text of this node."""
        ...

    @property
    def name(self) -> str:
        """Declared name of this node, or an empty string if it has none."""
        ...

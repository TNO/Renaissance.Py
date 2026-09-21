"""AI: Structural protocol describing the interface consumed by generic syntax-tree algorithms."""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, Self, runtime_checkable

from .semantic_kind import SemanticKind


@runtime_checkable
class NodeProtocol(Protocol):
    """Structural interface consumed by generic syntax-tree algorithms."""

    parser_kind: str
    semantic_kind: SemanticKind
    properties: Mapping[str, Any]
    children: Sequence[Self]
    signature: str
    name: str

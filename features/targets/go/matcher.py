"""AI: Structural matching protocol and helper for Go AST nodes."""

from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class NodeMatchProtocol(Protocol):
    """AI: Structural protocol describing the properties/children shape required for Go AST node matching."""

    properties: dict
    children: list[Self]


def is_match(src: NodeMatchProtocol, cmp: NodeMatchProtocol) -> bool:
    """AI: Structurally compare two Go AST nodes for a match."""

"""Fixture source modeling a Go AST node for CST/AST refactoring tests."""

from collections.abc import Sequence
from typing import Any, Self


class GoAstNode:
    """Base node type exposing Go AST children, properties, and rewrite metadata."""

    # direct access protocol
    expr: Self
    body: Sequence[Self]
    other: Sequence[Self]

    # rewrite protocol
    length: int
    offset: int
    name: str

    @property
    def properties(self) -> dict[str, Any]:
        """Return the rewrite metadata (length, offset, name) for this node."""
        return {"length": self.length, "offset": self.offset, "name": self.name}

    @property
    def children(self) -> list[Self]:
        """Return this node's direct child nodes (expr, body, other)."""
        return [self.expr, self.body, self.other]

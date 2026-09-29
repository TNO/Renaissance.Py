"""Structural protocol describing the pattern factory interface consumed by generic refactoring actions."""

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from .ast_node import ASTNode


@runtime_checkable
class PatternFactoryProtocol[NodeT, TranslationUnitT](Protocol):
    """Structural interface of a factory that builds pattern nodes from source text."""

    def create(self, text: str, kind: Callable[[ASTNode[NodeT, TranslationUnitT]], bool] | None = None) -> ASTNode[NodeT, TranslationUnitT]:
        """Create the pattern node for text.

        Args:
            text: The source text of the pattern.
            kind: Predicate selecting which node of the parsed text is returned. When omitted, the root is returned.

        Returns:
            The pattern node.

        """
        ...

    def create_declaration(self, text: str) -> ASTNode[NodeT, TranslationUnitT]:
        """Create the pattern node for the declaration in text."""
        ...

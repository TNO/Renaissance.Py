from collections.abc import Sequence
from typing import Protocol, Self, runtime_checkable

from renaissance.syntax_tree.syntax_node import SyntaxNode
from renaissance.syntax_tree.text_segment import TextSegment

# TODO: Do we only want to wrap the AST sequence matches in AST pattern matching?
#       or also the parser output?


@runtime_checkable
class Siblings[NodeType](TextSegment, Protocol):
    """Protocol for contiguous siblings, i.e., a range of syntax nodes.
    Siblings is a text segment.
    When the range of siblings is empty, the start and end offset of the text segment are the same.
    Yet, an offset within the text is available.

    Read-only access is enforced "as much as possible" by
    exposing only @property getters in the protocol
    """

    @property
    def syntax_nodes(self) -> Sequence[SyntaxNode[NodeType]]:
        """The sequence of SyntaxNodes corresponding to these siblings.
        """
        ...

    @property
    def parent(self) -> Self:
        """The parent of these siblings.

        The property 'parent' is not used to compare siblings.
        """
        ...

    @property
    def original_nodes(self) -> Sequence[NodeType]:
        """The sequence of original nodes of these siblings as produced by the parser.

        The property 'original_nodes' is not used to compare siblings.
        """
        ...

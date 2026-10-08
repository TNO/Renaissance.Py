"""Protocol defining syntax nodes such as AST, CST, and parse tree nodes."""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, Self, runtime_checkable

from renaissance.syntax_tree.text_segment import TextSegment


@runtime_checkable
class SyntaxNode[NodeType](TextSegment, Protocol):
    """Protocol for anything that represents syntax nodes.

    Syntax nodes include AST nodes, CST nodes, and parse tree nodes.
    A syntax node is a text segment.

    Read-only access is enforced "as much as possible" by
    exposing only @property getters in the protocol
    """

    @property
    def kind(self) -> str:
        """The textual representation of the kind of this node.

        The property 'kind' is used to compare syntax nodes.
        """
        ...

    @property
    def children(self) -> Sequence[Self]:
        """The children of this node.

        The read-only Sequence keeps the protocol covariant, so implementations may return a list.

        The property 'children' is used to compare syntax nodes.
        """
        ...

    @property
    def syntax_attributes(self) -> Mapping[str, Any]:
        """The syntax attributes of this node.

        The read-only Mapping keeps the protocol covariant, so implementations may return a dict.

        The property 'syntax_attributes' is used to compare syntax nodes.
        """
        ...

    @property
    def parent(self) -> Self | None:
        """The parent of this node.

        The parent should only be None when the node represents the top of a tree,
        such as a compilation unit.

        The property 'parent' is not used to compare syntax nodes.
        """
        ...

    @property
    def original_node(self) -> NodeType:
        """The original node as produced by the parser.

        The property 'original_node' is not used to compare syntax nodes.
        """
        ...

"""AI: Abstract base class for AST node implementations, with the shared traversal and rewrite protocol."""

from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from enum import Enum
from pathlib import Path
from typing import Any, Self

from renaissance.utils.ast_utils import format_node, next_sibling, preceding_sibling, process_node
from renaissance.utils.text_utils import TextUtils


# enum with ABORT, CONTINUE and SKIP
class VisitorResult(Enum):
    """AI: Signal how an AST traversal should continue after visiting a node."""

    ABORT = 0
    CONTINUE = 1
    SKIP = 2


class ASTReference[NodeT, TranslationUnitT]:
    """AI: Represent a reference from one AST node to another, along with the kind of reference."""

    def __init__(self, ast_node: ASTNode[NodeT, TranslationUnitT], ref_kind: str, properties: dict[str, Any]) -> None:
        """AI: Represent a reference from one AST node to another, along with the kind of reference."""
        self._node = ast_node
        self._ref_kind = ref_kind
        self._properties = properties

    @property
    def node(self) -> ASTNode[NodeT, TranslationUnitT]:
        """AI: Return the AST node this reference points from."""
        return self._node

    @property
    def ref_kind(self) -> str:
        """AI: Return the kind of this reference."""
        return self._ref_kind

    @property
    def properties(self) -> dict[str, Any]:
        """AI: Return this reference's additional properties."""
        return self._properties


# To make usage of the concrete class methods easier, ASTNode MUST NOT have ABSTRACT public classes!!
class ASTNode[NodeT, TranslationUnitT](ABC):
    """The base class to represent an AST node.

    It is an abstract class that should be inherited by concrete classes that represent specific AST nodes.
    """

    cache: dict[str, bytes] = {}

    def __init__(self, root: Self) -> None:
        """AI: Initialize a new AST node rooted at the given translation-unit-level node."""
        super().__init__()
        self._parent = None
        self._children: list[Self] = []
        self.show_props: bool = False
        self.translation_unit: TranslationUnitT | None = None
        self._kind: str = ""
        self._length: int = 0
        self._offset: int = 0
        self._filename: str = ""
        self.root: Self = root
        self._properties = {}
        self._name = ""
        self.node: NodeT | None = None
        self.indent = ""

    def __repr__(self):
        """AI: Return the formatted node representation."""
        return format_node(self)

    def is_part_of_translation_unit(self) -> bool:
        """AI: Return whether this node's filename matches its root node's filename."""
        return self.filename == self.root.filename

    @property
    def signature(self) -> str:
        """AI: Return this node's source code text, or an empty string if it has no filename or span."""
        start = self.offset
        end = self.extended_end_offset
        if start == end:
            return ""
        file = self.filename
        if not file:
            return ""
        return self.content(start, end)

    @property
    def text(self) -> str:
        """AI: Return this node's signature text shifted left to remove its leading indent."""
        return TextUtils.shift_left(self.signature, len(self.indent), start_line=1)

    def content(self, start: int, end: int) -> str:
        """AI: Return the decoded source text between start and end offsets in the root's file content."""
        content = self.root.binary_file_content()
        return str(content[start:end], sys.getfilesystemencoding())

    def binary_file_content(self, file_path: str | None = None) -> bytes:
        """AI: Return the raw bytes of file_path (or the root's filename), reading and caching it on first access."""
        if not file_path:
            file_path = self.root.filename
        try:
            return ASTNode.cache[file_path]
        except KeyError:
            with Path(file_path).open("rb") as f:
                content = f.read()
                ASTNode.cache[file_path] = content
                return content

    @property
    def preceding_sibling(self) -> Self | None:
        """AI: Return the sibling node immediately preceding this one, or None."""
        return preceding_sibling(self)

    @property
    def next_sibling(self) -> Self | None:
        """AI: Return the sibling node immediately following this one, or None."""
        return next_sibling(self)

    @property
    @abstractmethod
    def references(self) -> list[ASTReference[NodeT, TranslationUnitT]]:
        """AI: Return the references that this node points to."""

    @property
    @abstractmethod
    def referenced_by(self) -> list[ASTReference[NodeT, TranslationUnitT]]:
        """AI: Return the references that point to this node."""

    def get_ancestor(self, kind: str | re.Pattern[str]) -> Self | None:
        """AI: Return the nearest ancestor node whose kind matches the given kind pattern, or None."""
        pattern = re.compile(kind, re.IGNORECASE) if isinstance(kind, str) else kind
        parent = self.parent
        if not parent:
            return None
        if pattern.match(parent.kind):
            return parent
        return parent.get_ancestor(pattern)

    def is_descendant_of(self, node: Self) -> bool:
        """AI: Return whether this node is a descendant of node."""
        return node.is_ancestor_of(self)

    def is_ancestor_of(self, descendant: Self) -> bool:
        """AI: Return whether this node is an ancestor of descendant."""
        parent: Self = descendant.parent
        if parent == self:
            return True
        if not parent:
            return False
        return self.is_ancestor_of(parent)

    @staticmethod
    @abstractmethod
    def load(file_path: Path, extra_args: Sequence[str], working_dir: Path) -> ASTNode[NodeT, TranslationUnitT]:
        """AI: Parse the source file at file_path into an AST node."""

    @staticmethod
    @abstractmethod
    def load_from_text(text: str, file_name: str, extra_args: Sequence[str], working_dir: Path) -> ASTNode[NodeT, TranslationUnitT]:
        """AI: Parse source text (attributed to file_name) into an AST node."""

    @property
    def name(self) -> str:
        """AI: Return this node's name."""
        return self._name

    @property
    def filename(self) -> str:
        """AI: Return this node's source file name."""
        return self._filename

    # TODO: Is this the best name: offset, start_offset, begin_offset, ...?
    # TODO: Should offset return a slice object, https://docs.python.org/3/library/functions.html#slice, instead of an int?
    #       That would make it easier to get the text segment.
    @property
    def offset(self) -> int:
        """AI: Return the character offset where this node begins in the source text."""
        return self._offset

    @property
    def end_offset(self) -> int:
        """AI: Return the character offset where this node ends in the source text."""
        return self.offset + self.length

    # TODO: Is this the really best solution to ensure that the modified code has the proper layout?
    @property
    @abstractmethod
    def extended_end_offset(self) -> int:
        """AI: Return the character offset where this node's extended span (including trailing layout) ends."""

    @property
    def length(self) -> int:
        """AI: Return the length in characters of this node's source text."""
        return self._length

    @property
    def kind(self) -> str:
        """AI: Return this node's parser kind."""
        return self._kind

    @abstractmethod
    def matches_kind(self, node: Self) -> bool:
        """AI: Return whether node has the same kind as this node."""

    # TODO: What is the best name: properties, attributes, syntax_attributes, ...?
    @property
    def properties(self) -> dict[str, int | str]:  # TODO: Is int | str really sufficient? Shouldn't it be Any?
        """AI: Return this node's syntax properties."""
        return self._properties

    @property
    def parent(self) -> Self | None:
        """AI: Return this node's parent node, or None if it has none."""
        return self._parent

    @property
    @abstractmethod
    def is_statement(self) -> bool:
        """AI: Return whether this node represents a statement."""

    @property
    def children(self) -> list[Self]:
        """AI: Return this node's child nodes."""
        return self._children

    def process(self, function: Callable[[Self], None]) -> None:
        """AI: Apply function to this node and recursively to all of its descendants."""
        process_node(self, function)

    def accept(self, function: Callable[[Self], VisitorResult]) -> None:
        """Accept a visitor function and apply it to the current node and its children.

        Args:
            function (Callable[[Self], VisitorResult]): A function that takes an ASTNode as an argument and returns a VisitorResult.

        Returns:
            None

        """
        if function(self) == VisitorResult.CONTINUE:
            for child in self.children:
                child.accept(function)

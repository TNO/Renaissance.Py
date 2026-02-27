from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .text_utils import TextUtils

# enum with ABORT, CONTINUE and SKIP
class VisitorResult(Enum):
    ABORT = 0
    CONTINUE = 1
    SKIP = 2

class ASTReference:
    def __init__(
            self, ast_node: ASTNode, ref_kind: str, properties: dict[str, Any]
    ) -> None:
        self._node = ast_node
        self._ref_kind = ref_kind
        self._properties = properties

    @property
    def node(self) -> "ASTNode":
        return self._node

    @property
    def ref_kind(self) -> str:
        return self._ref_kind

    @property
    def properties(self) -> dict[str, Any]:
        return self._properties


# To make usage of the concrete class methods easier, ASTNode MUST NOT have ABSTRACT public classes!!
class ASTNode(ABC):
    cache: dict[str, bytes] = {}
    """
    The base class to represent an AST node.
    It is an abstract class that should be inherited by concrete classes that represent specific AST nodes.
    """

    def __init__(self, root: ASTNode) -> None:
        super().__init__()
        self._children = None
        self.show_props = None
        self._kind = None
        self._length = None
        self._offset = None
        self._filename = None
        self.root: ASTNode = root
        self._properties = {}
        self._name = ''
        self.indent = ''

    def __repr__(self):
        raw_lines = self.signature.splitlines()
        properties_text = '' if not self.show_props else self.properties
        prefix = " " if len(raw_lines) < 2 else f"\n    {self.indent}"
        formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
        return f"{self.indent}({self.kind}, {self.name}, {self.filename}[{self.offset}:{self.offset + self.length}]){properties_text}:{''.join(formatted_lines)}\n"

    def is_part_of_translation_unit(self) -> bool:
        return self.filename == self.root.filename

    @property
    def signature(self) -> str:
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
        return TextUtils.shift_left(
            self.signature, len(self.indent), start_line=1
        )

    def content(self, start: int, end: int) -> str:
        content = self.root.binary_file_content()
        return str(content[start:end], sys.getfilesystemencoding())

    def binary_file_content(self, file_path: str | None = None) -> bytes:
        if not file_path:
            file_path = self.root.filename
        try:
            return ASTNode.cache[file_path]
        except Exception:
            with open(file_path, "rb") as f:
                content = f.read()
                ASTNode.cache[file_path] = content
                return content

    @property
    def end_offset(self) -> int:
        return self.offset + self.length

    @property
    @abstractmethod
    def extended_end_offset(self) -> int:
        pass

    @property
    def preceding_sibling(self) -> ASTNode | None:
        parent = self.parent
        if not parent:
            return None
        siblings = parent.children
        index = siblings.index(self)
        return siblings[index - 1] if index > 0 else None

    @property
    @abstractmethod
    def references(self) -> list[ASTNode]:
        pass

    @property
    @abstractmethod
    def referenced_by(self) -> list[ASTNode]:
        pass

    @property
    def next_sibling(self) -> ASTNode | None:
        parent = self.parent
        if not parent:
            return None
        siblings = parent.children
        index = siblings.index(self)
        return siblings[index + 1] if index < len(siblings) - 1 else None

    def get_ancestor(self, kind: str | re.Pattern[str]) -> ASTNode | None:
        pattern = re.compile(kind, re.IGNORECASE) if isinstance(kind, str) else kind
        parent = self.parent
        if not parent:
            return None
        if pattern.match(parent.kind):
            return parent
        return parent.get_ancestor(pattern)

    def is_descendant_of(self, node: ASTNode) -> bool:
        return node.is_ancestor_of(self)

    def is_ancestor_of(self, descendant: ASTNode) -> bool:
        parent = descendant.parent
        if parent == self:
            return True
        if not parent:
            return False
        return self.is_ancestor_of(parent)

    @staticmethod
    @abstractmethod
    def load(
            file_path: Path, extra_args: list[str], working_dir: Path
    ) -> ASTNode:
        pass

    @staticmethod
    @abstractmethod
    def load_from_text(
            text: str, file_name: str, extra_args: list[str], working_dir: Path
    ) -> ASTNode:
        pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def offset(self) -> int:
        return self._offset

    @property
    def length(self) -> int:
        return self._length

    @property
    def kind(self) -> str:
        return self._kind

    @abstractmethod
    def matches_kind(self, node: ASTNode) -> bool:
        pass

    def get_frozen_properties(self) -> frozenset[tuple[str, Any]]:
        # TODO How to get type correct? How to get right of pyright: ignore comments?
        def freeze(value: Any) -> Any:
            if isinstance(value, dict):
                return frozenset(
                    (k, freeze(v)) for k, v in value.items()  # pyright: ignore
                )
            if isinstance(value, list):
                return tuple(
                    freeze(v)
                    for v in value  # pyright: ignore[reportUnknownVariableType]
                )
            return value

        return frozenset(freeze(self.properties))

    @property
    def properties(self) -> dict[str, int | str]:
        return self._properties

    @property
    def parent(self) -> ASTNode | None:
        return self._parent

    @property
    @abstractmethod
    def is_statement(self) -> bool:
        pass

    @property
    def children(self) -> list[ASTNode]:
        return self._children

    def process(self, function: Callable[[ASTNode], None]) -> None:
        function(self)
        for child in self.children:
            child.process(function)

    def accept(self, function: Callable[[ASTNode], VisitorResult]) -> None:
        """
        Accepts a visitor function and applies it to the current node and its children.

        Args:
            function (Callable[[ASTNode], VisitorResult]): A function that takes an ASTNode as an argument and returns a VisitorResult.

        Returns:
            None
        """
        if function(self) == VisitorResult.CONTINUE:
            for child in self.children:
                child.accept(function)

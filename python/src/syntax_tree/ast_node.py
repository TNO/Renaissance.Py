from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from functools import cache
from pathlib import Path
import re
import sys
from typing import Any, Callable, Optional, Sequence
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

    def get_node(self) -> "ASTNode":
        return self._node

    def get_ref_kind(self) -> str:
        return self._ref_kind

    def get_properties(self) -> dict[str, Any]:
        return self._properties


# To make usage of the concrete class methods easier, ASTNode MUST NOT have ABSTRACT public classes!!
class ASTNode(ABC):
    """
    The base class to represent an AST node.
    It is an abstract class that should be inherited by concrete classes that represent specific AST nodes.
    """

    def __init__(self, root: ASTNode) -> None:
        super().__init__()
        self.root: ASTNode = root
        self.cache: dict[str, bytes] = {}
        self.orelse=None
        self.properties = {}

    @property
    def expression(self):
        return self._expression

    def is_part_of_translation_unit(self) -> bool:
        return self.get_containing_filename() == self.root.get_containing_filename()

    def get_raw_signature(self) -> str:
        start = self.get_start_offset()
        end = self.get_extended_end_offset()
        if start == end:
            return ""
        file = self.get_containing_filename()
        if not file:
            return ""
        return self.get_content(start, end)

    def get_text(self) -> str:
        return TextUtils.shift_left(
            self.get_raw_signature(), self.get_indent(), start_line=1
        )

    def get_content(self, start: int, end: int) -> str:
        content = self.root.get_binary_file_content()
        return str(content[start:end], sys.getfilesystemencoding())

    def get_binary_file_content(self, file_path: Optional[str] = None) -> bytes:
        if not file_path:
            file_path = self.root.get_containing_filename()
        try:
            return self.cache[file_path]
        except Exception:
            with open(file_path, "rb") as f:
                content = f.read()
                self.cache[file_path] = content
                return content

    def get_end_offset(self) -> int:
        return self.get_start_offset() + self.get_length()

    def get_extended_end_offset(self) -> int:
        return self._get_extended_end_offset()

    def get_preceding_sibling(self) -> Optional[ASTNode]:
        parent = self.get_parent()
        if not parent:
            return None
        siblings = parent.children
        index = siblings.index(self)
        return siblings[index - 1] if index > 0 else None

    def get_next_sibling(self) -> Optional[ASTNode]:
        parent = self.get_parent()
        if not parent:
            return None
        siblings = parent.children
        index = siblings.index(self)
        return siblings[index + 1] if index < len(siblings) - 1 else None

    def get_ancestor(self, kind: str | re.Pattern[str]) -> Optional[ASTNode]:
        pattern = re.compile(kind, re.IGNORECASE) if isinstance(kind, str) else kind
        parent = self._get_parent()
        if not parent:
            return None
        if pattern.match(parent.kind):
            return parent
        return parent.get_ancestor(pattern)

    def is_descendant_of(self, node: ASTNode) -> bool:
        return node.is_ancestor_of(self)

    def is_ancestor_of(self, descendant: ASTNode) -> bool:
        parent = descendant.get_parent()
        if parent == self:
            return True
        if not parent:
            return False
        return self.is_ancestor_of(parent)

    @staticmethod
    @abstractmethod
    def load(
        file_path: Path, extra_args: Sequence[str], working_dir: Path
    ) -> ASTNode:
        pass

    @staticmethod
    @abstractmethod
    def load_from_text(
        text: str, file_name: str, extra_args: Sequence[str], working_dir: Path
    ) -> ASTNode:
        pass

    @property
    def name(self) -> str:
        return self._name

    def get_containing_filename(self) -> str:
        return self._get_containing_filename()

    def get_start_offset(self) -> int:
        return self._get_start_offset()

    def get_length(self) -> int:
        return self._get_length()

    @property
    def kind(self) -> str:
        return self._kind

    def matches_kind(self, node: ASTNode) -> bool:
        return self._matches_kind(node)

    @cache
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

        return frozenset(freeze(self._get_properties()))

    def get_properties(self) -> dict[str, int | str]:
        return self._get_properties()

    def get_parent(self) -> Optional[ASTNode]:
        return self._get_parent()

    def is_statement(self) -> bool:
        return self._is_statement()

    @property
    def children(self) -> Sequence[ASTNode]:
        return self._children

    def get_references(self) -> Sequence[ASTReference]:
        return self._get_references()

    def get_referenced_by(self) -> Sequence[ASTReference]:
        return self._get_referenced_by()

    @abstractmethod
    def _get_containing_filename(self) -> str:
        pass

    @abstractmethod
    def _get_start_offset(self) -> int:
        pass

    @abstractmethod
    def _get_extended_end_offset(self) -> int:
        pass

    @abstractmethod
    def _get_length(self) -> int:
        pass

    def _matches_kind(self, node: ASTNode) -> bool:
        return node.kind == self.kind

    @abstractmethod
    def _get_properties(self) -> dict[str, int | str |ASTNode]:
        pass

    @abstractmethod
    def _get_parent(self) -> Optional[ASTNode]:
        pass

    @abstractmethod
    def _is_statement(self) -> bool:
        pass

    @abstractmethod
    def _get_references(self) -> Sequence[ASTReference]:
        pass

    @abstractmethod
    def _get_referenced_by(self) -> Sequence[ASTReference]:
        pass

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

    def get_indent(self) -> int:
        if not self.is_part_of_translation_unit():
            return 0
        content = self.root.get_binary_file_content()
        offset = self.get_start_offset()
        return TextUtils.get_indent(content, offset)

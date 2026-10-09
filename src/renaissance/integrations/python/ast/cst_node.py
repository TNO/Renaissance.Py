"""AI: ASTNode implementation backed by libcst's concrete syntax tree."""

import io
import itertools
import sys
from pathlib import Path
from typing import Self

import libcst
from libcst import BaseCompoundStatement, BaseSmallStatement, ClassDef, CSTNode, FunctionDef, MetadataWrapper
from libcst.metadata import CodePosition, PositionProvider

from renaissance.integrations.python.ast.kinds import PYTHON_KIND_MAP
from renaissance.syntax_tree.semantic_kind import SemanticKind
from renaissance.utils.ast_utils import next_sibling, preceding_sibling


class PythonCstTranslationUnit:
    """AI: Parse Python source into a libcst tree with position lookups for AST-node wrapping."""

    def __init__(self, content, file_name: str) -> None:
        """AI: Parse Python source into a libcst tree with position lookups for AST-node wrapping."""
        # TODO: see docs/developer/architecture/position-consistency.md - exposes no buffer, so the rewriter derives its own.
        self.content = content
        self.encoding = sys.getfilesystemencoding()
        # newline="" splits on \n, \r\n and \r only, like libcst, and keeps each line ending.
        self._lines = io.StringIO(content, newline="").readlines()
        self._line_starts = list(itertools.accumulate((len(line.encode(self.encoding)) for line in self._lines), initial=0))
        self.file_name = file_name
        self.references_initialized = False
        self.wrapper = MetadataWrapper(libcst.parse_module(content))
        self.atu = self.wrapper.module
        self.spans = self.wrapper.resolve(PositionProvider)

    def _byte_offset(self, position: CodePosition) -> int:
        """Return the offset, in bytes of self.encoding, of a libcst position whose column counts characters.

        A position on the line after the last one (the end of a node that ends with the file) maps to the file's length.
        """
        line_index = position.line - 1
        if line_index >= len(self._lines):
            return self._line_starts[-1]
        return self._line_starts[line_index] + len(self._lines[line_index][: position.column].encode(self.encoding))

    def start_of(self, node: CSTNode) -> int:
        """Return the byte offset where node begins in the source text, or 0 if it has no position.

        A decorated function or class begins at its first decorator.
        """
        if isinstance(node, (ClassDef, FunctionDef)) and node.decorators:
            node = node.decorators[0]
        span = self.spans.get(node)
        return self._byte_offset(span.start) if span else 0

    def end_of(self, node: CSTNode) -> int:
        """Return the byte offset where node's code ends in the source text, or 0 if it has no position."""
        span = self.spans.get(node)
        return self._byte_offset(span.end) if span else 0

    def signature_of(self, node: CSTNode) -> str:
        """AI: Return the source code text corresponding to node, or an empty string on failure."""
        try:
            return self.atu.code_for_node(node)
        except Exception:
            return ""


class PythonCstNode:
    """AI: ASTNode implementation backed by libcst's concrete syntax tree."""

    def __init__(self, node: CSTNode, translation_unit: PythonCstTranslationUnit, parent=None) -> None:
        """AI: Wrap a libcst node as an AST node within the given translation unit."""
        self.parent = parent
        if parent and parent.root:
            self.root = parent.root
        else:
            self.root = self
        self.translation_unit = translation_unit
        self.node = node

        self.is_statement = isinstance(self.node, (BaseSmallStatement, BaseCompoundStatement))
        self.parser_kind = type(node).__name__
        self.semantic_kind = PYTHON_KIND_MAP.get(self.parser_kind, SemanticKind.NODE)

        self.children: list[Self] = [PythonCstNode(node, translation_unit, self) for node in node.children]
        self.properties = {}

        # for shower
        self.is_implicit = True
        self.show_props = False

        # for rewriter
        self.text = self.signature

    def __str__(self) -> str:
        """AI: Return the string representation of the wrapped CST node."""
        return str(self.node)

    def __repr__(self) -> str:
        """AI: Return the repr of the wrapped CST node."""
        return repr(self.node)

    @property
    def signature(self):
        """AI: Return the source code text of the wrapped CST node."""
        return self.translation_unit.signature_of(self.node)

    @property
    def offset(self):
        """AI: Return the character offset where this node begins in the source text."""
        return self.translation_unit.start_of(self.node)

    @property
    def length(self):
        """AI: Return the length in characters of this node's source text."""
        return self.end_offset - self.offset

    @property
    def end_offset(self):
        """AI: Return the character offset where this node ends in the source text."""
        return self.translation_unit.end_of(self.node)

    @property
    def extended_end_offset(self) -> int:
        """Return the end offset; trailing comments are found by the rewriter, as for the RST backend."""
        return self.end_offset

    @property
    def filename(self):
        """AI: Return the source file name of this node's translation unit."""
        return self.translation_unit.file_name

    @property
    def name(self):
        """AI: Return this node's class/function name, or an empty string if not applicable."""
        if isinstance(self.node, (ClassDef, FunctionDef)):
            return self.node.name.value
        return ""
        self.name = ""  # self._derive_name()

    @property
    def next_sibling(self) -> Self | None:
        """AI: Return the sibling node immediately following this one, or None."""
        return next_sibling(self)

    @property
    def preceding_sibling(self) -> Self | None:
        """AI: Return the sibling node immediately preceding this one, or None."""
        return preceding_sibling(self)

    @staticmethod
    def load(file_path: Path) -> PythonCstNode:
        """AI: Parse the Python source file at file_path into a PythonCstNode tree."""
        with Path(file_path).open() as file:
            content = file.read()
            return PythonCstNode.load_from_text(content, str(file_path))

    @staticmethod
    def load_from_text(
        text: str,
        file_name: str = "cst_snippet.py",
    ) -> PythonCstNode:
        """AI: Parse Python source text into a PythonCstNode tree, attributed to file_name."""
        translation_unit = PythonCstTranslationUnit(text, file_name=str(file_name))
        root_node = PythonCstNode(translation_unit.atu, translation_unit)
        return root_node

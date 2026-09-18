"""AI: ASTNode implementation backed by libcst's concrete syntax tree."""

from pathlib import Path
from typing import Self

import libcst
from libcst import BaseCompoundStatement, BaseSmallStatement, ClassDef, CSTNode, FunctionDef, MetadataWrapper
from libcst.metadata import WhitespaceInclusivePositionProvider

from renaissance.integrations.python.ast.kinds import PYTHON_KIND_MAP
from renaissance.integrations.python.ast.util import convert
from renaissance.syntax_tree.semantic_kind import SemanticKind
from renaissance.utils.ast_utils import next_sibling, preceding_sibling


class PythonCstTranslationUnit:
    """AI: Parse Python source into a libcst tree with position lookups for AST-node wrapping."""

    def __init__(self, content, file_name: str):
        """AI: Parse Python source into a libcst tree with position lookups for AST-node wrapping."""
        self.content = content
        self.lines = content.splitlines()
        self.file_name = file_name
        self.references_initialized = False
        self.wrapper = MetadataWrapper(libcst.parse_module(content))
        self.atu = self.wrapper.module
        self.spans = self.wrapper.resolve(WhitespaceInclusivePositionProvider)

    def start_of(self, node: CSTNode) -> int:
        """AI: Return the character offset where node begins in the source text."""
        span = self.spans.get(node)
        return convert(self.lines, span.start.line, span.start.column) if span else 0

    def end_of(self, node: CSTNode) -> int:
        """AI: Return the character offset where node ends in the source text."""
        span = self.spans.get(node)
        return convert(self.lines, span.end.line, span.end.column) if span else 0

    def signature_of(self, node: CSTNode) -> str:
        """AI: Return the source code text corresponding to node, or an empty string on failure."""
        try:
            return self.atu.code_for_node(node)
        except Exception:
            return ""


class PythonCstNode:
    """AI: ASTNode implementation backed by libcst's concrete syntax tree."""

    def __init__(self, node: CSTNode, translation_unit: PythonCstTranslationUnit, parent=None):
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

    def __str__(self):
        """AI: Return the string representation of the wrapped CST node."""
        return str(self.node)

    def __repr__(self):
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

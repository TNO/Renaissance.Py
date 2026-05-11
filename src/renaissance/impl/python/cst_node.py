from pathlib import Path
from typing import Self

import libcst
from libcst import BaseSmallStatement, BaseCompoundStatement, CSTNode, MetadataWrapper, ClassDef
from libcst import FunctionDef
from libcst.metadata import WhitespaceInclusivePositionProvider

from renaissance.impl.types import KIND_MAP, UnknownType
from renaissance.impl.python.util import convert
from renaissance.utils.ast_utils import preceding_sibling, next_sibling


class PythonCstTranslationUnit:
    def __init__(self, content, file_name: str):
        self.content = content
        self.lines = content.splitlines()
        self.file_name = file_name
        self.references_initialized = False
        self.wrapper = MetadataWrapper(libcst.parse_module(content))
        self.atu = self.wrapper.module
        self.spans = self.wrapper.resolve(WhitespaceInclusivePositionProvider)

    def start_of(self, node: CSTNode) -> int:
        span = self.spans.get(node)
        return convert(self.lines, span.start.line, span.start.column) if span else 0

    def end_of(self, node: CSTNode) -> int:
        span = self.spans.get(node)
        return convert(self.lines, span.end.line, span.end.column) if span else 0

    def signature_of(self, node: CSTNode) -> str:
        try:
            return self.atu.code_for_node(node)
        except:
            return ""


class PythonCstNode:
    def __init__(self, node: CSTNode, translation_unit: PythonCstTranslationUnit, parent=None):
        self.parent = parent
        if parent and parent.root:
            self.root = parent.root
        else:
            self.root = self
        self.translation_unit = translation_unit
        self.node = node

        self.is_statement = isinstance(self.node, (BaseSmallStatement, BaseCompoundStatement))

        # for matcher
        self.ast_type = KIND_MAP.get(type(node).__name__, UnknownType) #type(node))
        if self.ast_type ==UnknownType:
            print(f'"{type(node).__name__}": {type(node).__name__},')
        self.children: list[Self] = [PythonCstNode(node, translation_unit, self) for node in node.children]
        self.properties = {}

        # for shower
        self.is_implicit = True
        self.show_props = False

        # for rewriter
        self.text = self.signature

    def __str__(self):
        return str(self.node)

    def __repr__(self):
        return repr(self.node)

    @property
    def signature(self):
        return self.translation_unit.signature_of(self.node)

    @property
    def offset(self):
        return self.translation_unit.start_of(self.node)

    @property
    def length(self):
        return self.end_offset - self.offset

    @property
    def end_offset(self):
        return self.translation_unit.end_of(self.node)

    @property
    def filename(self):
        return self.translation_unit.file_name

    @property
    def name(self):
        if isinstance(self.node, (ClassDef, FunctionDef)):
            return self.node.name.value
        else:
            return ""
        self.name = ""  # self._derive_name()

    @property
    def next_sibling(self) -> Self | None:
        return next_sibling(self)

    @property
    def preceding_sibling(self) -> Self | None:
        return preceding_sibling(self)

    @staticmethod
    def load(file_path: Path) -> "PythonCstNode":
        with open(file_path, "r") as file:
            content = file.read()
            return PythonCstNode.load_from_text(content, str(file_path))

    @staticmethod
    def load_from_text(
        text: str,
        file_name: str = "cst_snippet.py",
    ) -> "PythonCstNode":
        translation_unit = PythonCstTranslationUnit(text, file_name=str(file_name))
        root_node = PythonCstNode(translation_unit.atu, translation_unit)
        return root_node

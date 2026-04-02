from fileinput import filename

from pathlib import Path
from typing import Any, Sequence, Self, Callable

import libcst
from libcst import BaseSmallStatement, BaseCompoundStatement, IndentedBlock, CSTNode, FunctionDef, ClassDef
from libcst.display import dump

from renaissance.syntax_tree.match_finder import find_in_list, IRRELEVANT_PROPS
from renaissance.utils.node_util import preceding_sibling, next_sibling

class PythonCstTranslationUnit:
    def __init__(self, content, file_name: str):
        self.content = content
        self.atu = libcst.parse_module(content)
        self.file_name = file_name
        self.references_initialized = False



class PythonCstNode:
    def __init__(self, node: CSTNode, translation_unit: PythonCstTranslationUnit = None, parent=None):
        self.root = parent.root if parent and parent.root else self
        self.node = node
        self.parent = parent
        self.translation_unit = translation_unit
        self.kind = type(node).__name__
        self.indent = ""
        self.name = "" #self._derive_name()
        self.show_props = False
        self.children: list[Self] =[PythonCstNode(node, translation_unit, self) for node in node.children]
        self.properties = {}
        self.offset = node.code_span.start
        self.length = node.code_span.length
        self.end_offset = self.offset + self.length
        self.is_statement = isinstance(self.node, (BaseSmallStatement,BaseCompoundStatement))
        self.signature =self.root.node.code_for_node(node)


    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self.kind == other.kind
            and self.match_props(other.properties)
            and self.match_children(other.children)
        )

    def __contains__(self, item):
        if not isinstance(item, list):
            item = [item]
        return find_in_list(self.children, item)

    def __getitem__(self, key):
        """Allow indexing/slicing into node to access children.

        Usage: node[0] == node.children[0]
        """
        return self.children[key]
    def __repr__(self):
        raw_lines = self.signature.splitlines()
        properties_text = "" if not self.show_props else self.properties
        prefix = " " if len(raw_lines) < 2 else f"\n    {self.indent}"
        formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
        return f"{self.indent}({self.kind}, {self.name}, {self.filename}[{self.offset}:{self.offset + self.length}]){properties_text}:{''.join(formatted_lines)}\n"

    @property
    def next_sibling(self) -> Self | None:
        return next_sibling(self)

    @property
    def preceding_sibling(self) -> Self | None:
        return preceding_sibling(self)

    def process(self, function: Callable[[Self], None]) -> None:
        function(self)
        for child in self.children:
            child.process(function)


    def match_props(self, properties) -> bool:
        all_keys = (self.properties.keys() | properties.keys()) - IRRELEVANT_PROPS
        return all(self.properties.get(n) == properties.get(n) for n in all_keys)

    def match_children(self, children):
        return all(i< len(self.children) and self[i] == child for i, child in enumerate(children))

    @staticmethod
    def load(file_path: Path,
             extra_args:list[str] = None,
            working_dir:str = None
    ) -> "PythonCstNode":
        with open(file_path, "r") as file:
            content = file.read()
            return PythonCstNode.load_from_text(content, str(file_path), extra_args, working_dir)

    @staticmethod
    def load_from_text(
        text: str,
        file_name: str = "test.py",
        extra_args:list[str] = None,
        working_dir:str = None
    ) -> "PythonCstNode":
        translation_unit = PythonCstTranslationUnit(text, file_name=str(file_name))
        root_node = PythonCstNode(translation_unit.atu, translation_unit, None)
        return root_node

    @property
    def referenced_by(self) :
        return []

    @property
    def references(self):
        return []
    @property
    def text(self) -> str:
        return self.signature
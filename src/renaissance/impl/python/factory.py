from pathlib import Path
from typing import Sequence

import tree_sitter_python
from ast_comments import *
from libcst import SimpleStatementLine

from renaissance.impl.types import KIND_MAP, MatchAll, MatchOne
from renaissance.impl import MATCH_ALL, MATCH_ONE
from renaissance.impl.python.ast_node import ASTExtension
from renaissance.impl.python.cst_node import PythonCstNode
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.tree_sitter.adapter import TreeSitterAdapter
from renaissance.impl.tree_sitter.lst import LSTNode
from renaissance.syntax_tree.match_finder import AstProtocol, is_match
from renaissance.utils.ast_utils import replace_dollar, use_dollar

_MATCH_ALL_RE = re.compile(r"^" + re.escape(MATCH_ALL) + r"\w+$")
_MATCH_ONE_RE = re.compile(r"^" + re.escape(MATCH_ONE) + r"\w+$")

SHOW_NODE = False


class PythonPattern(AstProtocol):

    def __init__(self, node):
        self.node: PythonRstNode = node
        if type(node) is str:
            print(node)
            return
        self.kind: str = self.derive_kind(node.node)
        self.properties: dict = node.properties
        self.children: list[PythonPattern] = [PythonPattern(node) for node in node.children]
        self.signature: str = node.signature
        if hasattr(node, "name") and node.name:
            self.name: str = use_dollar(node.name)
        else:
            self.name = ""

    def __eq__(self, other: AstProtocol) -> bool:
        return is_match(self, other)

    def __repr__(self):
        return use_dollar(str(self.node))

    def derive_kind(self, ast_node: AST) -> str:
        signature = ""
        if isinstance(ast_node, ast.arg):
            signature = ast_node.arg
        elif isinstance(ast_node, ast.Name):
            signature = ast_node.id
        elif isinstance(ast_node, ast.Expr) and isinstance(ast_node.value, ast.Name):
            signature = ast_node.value.id
        if _MATCH_ALL_RE.match(signature):
            return MatchAll.__name__
        elif _MATCH_ONE_RE.match(signature):
            return MatchOne.__name__
        if isinstance(ast_node, LSTNode):
            return ast_node.kind
        else:
            return KIND_MAP.get(type(ast_node).__name__, type(ast_node)).__name__


class PythonFactory:

    def __init__(self, clazz: type[PythonRstNode | PythonCstNode | LSTNode | AST]) -> None:
        self.clazz = clazz
        if clazz == LSTNode:
            clazz.load_from_text = self.load_from_lst
        elif clazz == AST:
            clazz.load_from_text = ASTExtension.load_from_ast
            # matcher
            clazz.node = ASTExtension.ast_node
            clazz.kind = ASTExtension.ast_kind
            clazz.ast_type = ASTExtension.ast_type
            clazz.properties = ASTExtension.ast_properties
            clazz.children = ASTExtension.ast_children
            clazz.signature = ASTExtension.ast_signature

            # writer
            clazz.text = ASTExtension.ast_signature
            clazz.filename = "dummy.py"

            # shower
            clazz.is_implicit = True
            clazz.show_props = False
            clazz.indent = ""

    def create(self, file_path: Path) -> PythonRstNode | PythonCstNode:
        atu = self.clazz.load(file_path=file_path)
        assert isinstance(atu, self.clazz)
        return atu

    def create_from_text(self, text: str, file_name: str = "snippet.py") -> PythonRstNode | PythonCstNode | LSTNode | AST:

        atu = self.clazz.load_from_text(text, file_name)
        assert isinstance(atu, self.clazz)
        return atu

    @staticmethod
    def load_from_lst(text, file):
        adapter = TreeSitterAdapter(tree_sitter_python)
        tree = adapter.parse_code(text)
        return adapter.to_lst(text, tree).root


class PythonPatternFactory:

    def __init__(self, factory: PythonFactory):
        self.factory = factory

    def _create(self, text: str) -> PythonPattern:
        return PythonPattern(self.factory.create_from_text(text, "pattern.py"))

    def create(self, text: str) -> PythonPattern:
        text = replace_dollar(text)
        return self._create(text)

    def create_statements(self, text: str) -> Sequence[PythonPattern]:
        atu = self.create(text)
        return atu.children

    def create_statement(self, text: str) -> PythonPattern:
        stmt = self.create_statements(text)[-1]
        if isinstance(stmt.node.node, SimpleStatementLine) or (
            isinstance(stmt.node, LSTNode) and stmt.node.kind == "Expr" and stmt.children[0].node.kind != "Call"
        ):
            return stmt.children[0]
        else:
            return stmt
        # return stmt

    def create_expression(self, text: str) -> PythonPattern:
        my_pattern = self.create_statement(text)
        if isinstance(my_pattern.node, PythonRstNode):
            return PythonPattern(my_pattern.node.expression)
        elif isinstance(my_pattern.node, LSTNode):
            return PythonPattern(my_pattern.node)
        elif isinstance(my_pattern.node, PythonCstNode):
            return PythonPattern(my_pattern.node.children[-1])
        else:
            return PythonPattern(my_pattern.node.children[0])

    def create_decorators(self, param):
        return self.create_statement(param + "\ndef test(): pass").children[2]

    @staticmethod
    def create_kwargs(kw_str) -> Sequence[PythonPattern]:
        call = ast.parse(f"fun({replace_dollar(kw_str)})", "kwarg_pattern.py", type_comments=True).body[0]
        if isinstance(call, Expr) and isinstance(call.value, Call):
            return [PythonPattern(PythonRstNode(kwarg)) for kwarg in call.value.keywords]
        return []

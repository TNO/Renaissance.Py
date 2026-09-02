import ast
import re
from collections.abc import Sequence
from pathlib import Path

import tree_sitter_python
from libcst import SimpleStatementLine

from renaissance.impl import MATCH_ALL, MATCH_ONE
from renaissance.impl.python.ast_node import ASTExtension
from renaissance.impl.python.cst_node import PythonCstNode
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.tree_sitter.adapter import TreeSitterAdapter
from renaissance.impl.tree_sitter.lst import LSTNode
from renaissance.impl.types import Arg, DeclarationExpression, ExpressionStatement, MatchAll, MatchOne, Name, Type
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
        self.ast_type: Type = self.derive_type(node)

        self.properties: dict = node.properties
        self.children: list[PythonPattern] = [PythonPattern(node) for node in node.children]
        self.signature: str = node.signature
        if hasattr(node, "name") and node.name:
            self.name: str = use_dollar(node.name)
        else:
            self.name = ""

    def __eq__(self, other: AstProtocol) -> bool:
        return is_match(other, self)

    def __repr__(self):
        return use_dollar(str(self.node))

    def derive_type(self, node) -> str:
        # signature = ""
        # if isinstance(node.ast_type(), Argument):
        #     signature = node.node.arg
        # elif isinstance(node.ast_type(), Name):
        #     signature = node.node.value
        # elif isinstance(node.ast_type(), ExpressionStatement) and isinstance(node.node.value, ast.Name):
        #     signature = node.node.value.id
        # if _MATCH_ALL_RE.match(signature):
        #     return MatchAll
        # elif _MATCH_ONE_RE.match(signature):
        #     return MatchOne
        # if isinstance(node, LSTNode):
        #     return node.ast_type
        # else:
        #     return node.ast_type
        if isinstance(node, ast.arg):
            signature = node.arg
        elif isinstance(node, ast.Name):
            signature = node.id
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Name):
            signature = node.value.id
        elif isinstance(node, ast.AST):
            signature = str(node)
        else:
            signature = node.name

        if node.ast_type in [DeclarationExpression, ExpressionStatement, Name, Arg]:
            if _MATCH_ALL_RE.match(signature):
                return MatchAll
            if _MATCH_ONE_RE.match(signature):
                return MatchOne

        return node.ast_type


class PythonFactory:
    def __init__(self, clazz: type[PythonRstNode | PythonCstNode | LSTNode | ast.AST]) -> None:
        self.clazz = clazz
        if clazz == LSTNode:
            clazz.load_from_text = self.load_from_lst
        elif clazz == ast.AST:
            clazz.load_from_text = ASTExtension.load_from_ast
            # matcher
            clazz.node = ASTExtension.ast_node

            # clazz.name = ASTExtension.ast_name
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

    def create_from_text(self, text: str, file_name: str = "snippet.py") -> PythonRstNode | PythonCstNode | LSTNode | ast.AST:

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
        if isinstance(stmt.node.node, SimpleStatementLine):
            return stmt.children[0]
        return stmt
        # return stmt

    def create_expression(self, text: str) -> PythonPattern:
        my_pattern = self.create_statement(text)
        if isinstance(my_pattern.node, PythonRstNode):
            return PythonPattern(my_pattern.node.expression)
        if isinstance(my_pattern.node, LSTNode) or isinstance(my_pattern.node, PythonCstNode):
            return PythonPattern(my_pattern.node.children[-1])
        return PythonPattern(my_pattern.node.children[0])

    def create_decorators(self, param):
        return self.create_statement(param + "\ndef test(): pass").children[2]

    @staticmethod
    def create_kwargs(kw_str) -> Sequence[PythonPattern]:
        call = ast.parse(f"fun({replace_dollar(kw_str)})", "kwarg_pattern.py", type_comments=True).body[0].value
        return [PythonPattern(PythonRstNode(kwarg)) for kwarg in call.keywords]

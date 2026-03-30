import re
from typing import Sequence, Self

from ast_comments import *

from renaissance.impl import MATCH_ALL, MATCH_ONE
from renaissance.impl.python.python_ast_node import PythonASTNode
from renaissance.syntax_tree import ASTFactory, ASTNode
from renaissance.syntax_tree.match_finder import AstProtocol, is_match
from renaissance.utils.node_util import replace_dollar

_MATCH_ALL_RE = re.compile(r"^" + re.escape(MATCH_ALL) + r"\w+$")
_MATCH_ONE_RE = re.compile(r"^" + re.escape(MATCH_ONE) + r"\w+$")

SHOW_NODE = False

class PythonPattern(AstProtocol):

    def __init__(self, node):

        self.node = node
        self.kind: str =self.derive_kind(node.node)
        self.properties: dict =node.properties
        self.children: list[Self] =[PythonPattern(node) for node in node.children]
        self.signature: str = node.signature
        self.name: str = node.name.replace(MATCH_ALL, "$$").replace(MATCH_ONE, "$")
    def __eq__(self, other:AstProtocol)-> bool:
        return is_match(other, self)
    def __repr__(self):
        return str(self.node).replace(MATCH_ALL, "$$").replace(MATCH_ONE, "$")

    def derive_kind(self, node) -> str:
        signature = ""
        if isinstance(node, ast.arg):
            signature = node.arg
        elif isinstance(node, ast.Name):
            signature = node.id
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Name):
            signature = node.value.id
        if _MATCH_ALL_RE.match(signature):
            return MATCH_ALL
        elif _MATCH_ONE_RE.match(signature):
            return MATCH_ONE
        return self.node.kind

class PythonPatternFactory:

    def __init__(self, factory: ASTFactory):
        self.factory = factory

    @staticmethod
    def _create(text: str) -> PythonPattern:
        return PythonPattern(PythonASTNode.load_from_text(text))

    def create(self, text: str) -> PythonPattern:
        text = replace_dollar(text)
        return self._create(text)

    def create_statements(self, text: str) -> Sequence[PythonPattern]:
        return self.create(text).children

    def create_statement(self, text: str) -> PythonPattern:
        return self.create_statements(text)[-1]

    def create_expression(self, text: str) -> ASTNode:
        return PythonPattern(self.create_statement(text).node.expression)

    def create_decorators(self, param):
        return self.create_statement(param + "\ndef test(): pass").children[2]

    @staticmethod
    def create_kwargs(kw_str) -> Sequence[PythonPattern]:
        call = ast.parse(f"fun({replace_dollar(kw_str)})", "snippet.py", type_comments=True).body[0]
        if isinstance(call, Expr) and isinstance(call.value, Call):
            return [PythonPattern(PythonASTNode(kwarg)) for kwarg in call.value.keywords]
        return []

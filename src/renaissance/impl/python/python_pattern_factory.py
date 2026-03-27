from typing import Sequence, Self

from ast_comments import *

from renaissance.impl.python import PythonASTNode
from renaissance.syntax_tree import ASTFactory, ASTNode
from renaissance.syntax_tree.match_finder import AstProtocol, is_match
from renaissance.utils.node_util import replace_dollar

SHOW_NODE = False

class PythonPattern(AstProtocol):

    def __init__(self, node):
        self.node = node
        self.kind: str =node.kind
        self.properties: dict =node.properties
        self.children: list[Self] =[PythonPattern(node) for node in node.children]
        self.signature: str = node.signature
        self.name: str = node.name
    def __eq__(self, other:AstProtocol)-> bool:
        return is_match(other, self)

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
        return self.create_statement(param + "\ndef test(): pass")[2]

    @staticmethod
    def create_kwargs(kw_str) -> Sequence[PythonPattern]:
        call = ast.parse(f"fun({replace_dollar(kw_str)})", "snippet.py", type_comments=True).body[0]
        if isinstance(call, Expr) and isinstance(call.value, Call):
            return [PythonPattern(PythonASTNode(kwarg)) for kwarg in call.value.keywords]
        return []

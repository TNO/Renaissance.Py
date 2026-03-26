from typing import Sequence

from ast_comments import *

from renaissance.impl.python import PythonASTNode
from renaissance.syntax_tree import ASTFactory, ASTNode
from renaissance.utils.node_util import replace_dollar

SHOW_NODE = False


class PythonPatternFactory:

    def __init__(self, factory: ASTFactory):
        self.factory = factory

    @staticmethod
    def _create(text: str) -> PythonASTNode:
        return PythonASTNode.load_from_text(text)

    def create(self, text: str) -> PythonASTNode:
        text = replace_dollar(text)
        return self._create(text)

    @staticmethod
    def create_python_pattern(text: str) -> PythonASTNode:
        text = replace_dollar(text)
        return PythonASTNode(parse(text).body[0])

    def create_statements(self, text: str) -> Sequence[PythonASTNode]:
        return self.create(text).children

    def create_statement(self, text: str) -> PythonASTNode:
        return self.create_statements(text)[-1]

    def create_expression(self, text: str) -> ASTNode:
        return self.create_statement(text).expression

    def create_decorators(self, param):
        return self.create_statement(param + "\ndef test(): pass")[2]

    @staticmethod
    def create_kwargs(kw_str) -> Sequence[PythonASTNode]:
        call = ast.parse(f"fun({replace_dollar(kw_str)})", "snippet.py", type_comments=True).body[0]
        if isinstance(call, Expr) and isinstance(call.value, Call):
            return [PythonASTNode(kwarg) for kwarg in call.value.keywords]
        return []

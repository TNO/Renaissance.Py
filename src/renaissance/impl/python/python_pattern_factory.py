from typing import Sequence

from ast_comments import *
from renaissance.syntax_tree import ASTFactory, ASTNode
from renaissance.utils.node_util import replace_dollar

SHOW_NODE = False

class PythonPattern:
    def __init__(self, node):
        self.node = node


class PythonPatternFactory:

    def __init__(self, factory: ASTFactory):
        self.factory = factory

    @staticmethod
    def _create(text: str) -> PythonPattern:
        return PythonPattern.load_from_text(text)

    def create(self, text: str) -> PythonPattern:
        text = replace_dollar(text)
        return self._create(text)

    @staticmethod
    def create_python_pattern(text: str) -> PythonPattern:
        text = replace_dollar(text)
        return PythonPattern(parse(text).body[0])

    def create_statements(self, text: str) -> Sequence[PythonPattern]:
        return self.create(text).children

    def create_statement(self, text: str) -> PythonPattern:
        return self.create_statements(text)[-1]

    def create_expression(self, text: str) -> ASTNode:
        return self.create_statement(text).expression

    def create_decorators(self, param):
        return self.create_statement(param + "\ndef test(): pass")[2]

    @staticmethod
    def create_kwargs(kw_str) -> Sequence[PythonPattern]:
        call = ast.parse(f"fun({replace_dollar(kw_str)})", "snippet.py", type_comments=True).body[0]
        if isinstance(call, Expr) and isinstance(call.value, Call):
            return [PythonPattern(kwarg) for kwarg in call.value.keywords]
        return []

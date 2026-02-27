import ast
from typing import Sequence

from renaissance.common import Stream
from renaissance.impl.python import PythonASTNode
from renaissance.impl.python.python_ast_node import PythonTranslationUnit
from renaissance.syntax_tree import ASTFactory, ASTNode
from renaissance.utils.node_util import replace_dollar

SHOW_NODE = False


class PythonPatternFactory:

    def __init__(
            self,
            factory: ASTFactory,
            ref_node: ASTNode | None = None,
            language: str = "python",
    ):
        self.factory = factory
        if ref_node:
            offset = (
                Stream(ref_node.children)
                .filter(ASTNode.is_part_of_translation_unit)
                .map(lambda n: n.offset)
                .reduce(min)
                .or_else(0)
            )

        else:
            self.language = language
            self.header = ""

    def create_expression(
            self, text: str, extra_declarations=None
    ) -> ASTNode:
        if extra_declarations is None:
            extra_declarations = []
        text = replace_dollar(text)
        return PythonASTNode(ast.parse(text).body[0].value)

    def create_statements(
            self,
            text: str,
            types=None,
            extra_declarations=None,
            kind: str = ".*",
    ) -> Sequence[ASTNode]:
        if extra_declarations is None:
            extra_declarations = []
        if types is None:
            types = []
        text = replace_dollar(text)
        result = []

        root = PythonTranslationUnit(text, "snippet.py")
        return PythonASTNode(root.atu).children

    def create_python_pattern(self, text: str) -> PythonASTNode:
        # create python node from string
        # the output could be different, the comments are removed
        # Return PythonASTNode
        text = replace_dollar(text)
        return PythonASTNode(ast.parse(text).body[0])

    def create(self, text: str, kind: str|None = None) -> ASTNode:
        # create python from text
        # the comments are removed
        # Return Module
        text = replace_dollar(text)
        return self._create(text)

    def create_statement(
            self,
            text: str,
            types=None,
            extra_declarations=None,
            kind: str = ".*",
    ) -> ASTNode:
        if extra_declarations is None:
            extra_declarations = []
        if types is None:
            types = []
        statements = self.create_statements(text, types, extra_declarations, kind)
        assert len(statements) == 1, "Only one statement is expected"
        return statements[0]

    def _create(self, text: str) -> ASTNode:
        atu = self.factory.create_from_text(text, "test.py")
        return atu.children[0]

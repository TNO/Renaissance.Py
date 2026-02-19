import ast
import re
from typing import Optional, Sequence

from common.stream import Stream
from impl.python.python_ast_node import PythonTranslationUnit
from syntax_tree.ast_node import MATCH_ALL, MATCH_ONE
from impl.python import PythonASTNode
from syntax_tree.ast_node import ASTNode
from syntax_tree.ast_shower import ASTShower

from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_finder import ASTFinder
from utils.node_util import replace_dollar

SHOW_NODE = False


class PythonPatternFactory:

    def __init__(
        self,
        factory: ASTFactory,
        ref_node: Optional[ASTNode] = None,
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
        self, text: str, extra_declarations: Sequence[str] = []
    ) -> ASTNode:
        text = replace_dollar(text)
        return PythonASTNode(ast.parse(text).body[0].value)



    def create_statements(
        self,
        text: str,
        types: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        kind: str = ".*",
    ) -> Sequence[ASTNode]:
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

    def create(self, text: str, kind: Optional[str] = None) -> ASTNode:
        # create python from text
        # the comments are removed
        # Return Module
        text = replace_dollar(text)
        return self._create(text)

    def create_statement(
        self,
        text: str,
        types: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        kind: str = ".*",
    ) -> ASTNode:
        statements = self.create_statements(text, types, extra_declarations, kind)
        assert len(statements) == 1, "Only one statement is expected"
        return statements[0]

    def _create(self, text: str) -> ASTNode:
        atu = self.factory.create_from_text(text, "test.py")
        if SHOW_NODE:
            ASTShower.show_node(atu)
        return atu.children[0]


if __name__ == "__main__":
    print(
        PythonPatternFactory._get_dollar_keywords_from_text(
            "struct $type;struct $name; $type a = $name; int b = 4; $$x = $$y"
        )
    )
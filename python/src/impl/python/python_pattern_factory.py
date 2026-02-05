import ast
import re
from typing import Optional, Sequence

from common.stream import Stream
from impl import MATCH_ALL, MATCH_ONE
from impl.python import PythonASTNode
from syntax_tree.ast_node import ASTNode
from syntax_tree.ast_shower import ASTShower

from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_finder import ASTFinder

SHOW_NODE = False


class PythonPatternFactory:

    def __init__(
        self,
        factory: ASTFactory,
        ref_node: Optional[ASTNode] = None,
        language: str = "python",
    ):
        self.factory = factory
        # collect includes #defines  and var decl from the refNode
        if ref_node:
            offset = (
                Stream(ref_node.children)
                .filter(ASTNode.is_part_of_translation_unit)
                .filter(
                    lambda c: not ASTFinder.matches_kind(
                        c, "(?i)Macro.*|Inclusion_?Directive"
                    )
                )
                .map(lambda n: n.offset)
                .reduce(min)
                .or_else(0)
            )
           # self.header = ref_node.get_content(0, offset) + "\n"
            # self.header += (
            #     Stream(ref_node.get_children())
            #     .filter(ASTNode.is_part_of_translation_unit)
            #     .filter(
            #         lambda c: ASTFinder.matches_kind(
            #             c, "(?i)(Function|Var|Typedef)_?Decl"
            #         )
            #     )
            #     .filter(
            #         lambda c: ASTFinder.find_kind(c, "(?i)Compound_?Stmt").count() == 0
            #     )
            #     .map(lambda c: c.get_text() + ";")
            #     .collect(lambda n: "\n".join(n))
            #     + "\n"
            # )
        else:
            self.language = language
            self.header = ""
        # print(self.header)



    def create_expression(
        self, text: str, extra_declarations: Sequence[str] = []
    ) -> ASTNode:
        text = text.replace('$$', MATCH_ALL).replace('$', MATCH_ONE)
        return PythonASTNode(ast.parse(text).body[0].value)

    def create_statements(
        self,
        text: str,
        types: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        kind: str = ".*",
    ) -> Sequence[ASTNode]:
        text = text.replace('$$', MATCH_ALL).replace('$', MATCH_ONE)
        result = []
        for node in ast.parse(text).body:
            result.append(PythonASTNode(node))
        return result

    def create_python_pattern(self, text: str) -> PythonASTNode:
        # create python node from string
        # the output could be different, the comments are removed
        # Return PythonASTNode
        text = text.replace('$$', MATCH_ALL).replace('$', MATCH_ONE)
        return PythonASTNode(ast.parse(text).body[0])

    def create(self, text: str, kind: Optional[str] = None) -> ASTNode:
        # create python from text
        # the comments are removed
        # Return Module
        text = text.replace('$$', MATCH_ALL).replace('$', MATCH_ONE)
        return self._create(text)

    def create_statement(
        self,
        text: str,
        types: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        kind: str = ".*",
    ) -> ASTNode:
        statements = list(self.create_statements(text, types, extra_declarations, kind))
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
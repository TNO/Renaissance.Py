import ast
import re
from typing import Optional, Sequence

from common.stream import Stream
from .python_ast_node import PythonASTNode, MATCH_ALL, MATCH_ONE
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
                .map(ASTNode.get_start_offset)
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


    def create_declarations(
        self,
        text: str,
        types: Sequence[str] = [],
        parameters: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        declarations: Sequence[str] = [],
    ):
        keywords = PythonPatternFactory._get_keywords_from_text(text)
        keywords = [
            k
            for k in keywords
            if not any(k in ed for ed in extra_declarations)
            and not any(k in ed for ed in parameters)
            and not any(k in ed for ed in types)
            and not any(k in ed for ed in declarations)
        ]
        return self._create_body(
            text, types, [*parameters, *keywords], extra_declarations, "(?i).*DECL.*"
        )

    def create_declaration(
        self,
        text: str,
        types: Sequence[str] = [],
        parameters: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        declarations: Sequence[str] = [],
    ) -> ASTNode:
        result = self.create_declarations(
            text, types, parameters, extra_declarations, declarations
        )
        assert len(result) > 0, "At least one declaration is expected"
        return result[0]

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

    def _create_body(
        self,
        text: str,
        types: Sequence[str],
        parameters: Sequence[str],
        extra_declarations: Sequence[str],
        kind: str,
    ) -> list[ASTNode]:
        full_text = (
            self.header + "\n".join(PythonPatternFactory._to_typedef(types)) + "\n"
            "\n".join(PythonPatternFactory._to_declaration(parameters)) + "\n"
            "\n".join(extra_declarations) + "\n"
            "\nvoid " + PythonPatternFactory.reserved_function_name + "(){\n" + text + "\n}"
        )
        root = self._create(full_text)

        # from the children of the compound statement that contains the text, get for each child the first
        # node of the specified kind

        return (
            Stream(
                ASTFinder.find_kind(root.children[-1], "(?i)COMPOUND_?STMT")
                .find_first()
                .get()
                .children
            )
            .filter(ASTNode.is_part_of_translation_unit)
            .map(lambda n: ASTFinder.find_kind(n, kind).find_first().get())
            .to_list()
        )

    def _create(self, text: str) -> ASTNode:
        atu = self.factory.create_from_text(text, "test.py")
        if SHOW_NODE:
            ASTShower.show_node(atu)
        return atu

    @staticmethod
    def _get_keywords_from_text(text: str) -> Sequence[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r"\${0,2}[a-zA-Z]\w*")
        return list(
            k
            for k in set(re.findall(pattern, text))
            if k not in PythonPatternFactory.RESERVED_KEYWORDS
        )

    @staticmethod
    def _get_dollar_keywords_from_text(text: str) -> Sequence[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r"\${1,2}[a-zA-Z]\w*")
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_non_dollar_keywords_from_text(
        text: str, prefix: str = "void* ", postfix: str = ";"
    ) -> Sequence[str]:
        pattern = re.compile(r"[^\$][a-zA-Z]\w*")
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _to_declaration(
        keywords: Sequence[str], prefix: str = "int ", postfix: str = ";"
    ) -> Sequence[str]:
        return [prefix + keyword + postfix for keyword in keywords]

    @staticmethod
    def _to_typedef(
        keywords: Sequence[str], prefix: str = "typedef int ", postfix: str = ";"
    ) -> Sequence[str]:
        return [prefix + keyword + postfix for keyword in keywords]




if __name__ == "__main__":
    print(
        PythonPatternFactory._get_dollar_keywords_from_text(
            "struct $type;struct $name; $type a = $name; int b = 4; $$x = $$y"
        )
    )
    # factory = ASTFactory(ClangASTNode)
    # patternFactory = CPatternFactory(factory)
    # ASTShower.show_node(patternFactory.create_expression('a == $hallo'))

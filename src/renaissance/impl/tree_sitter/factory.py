from collections.abc import Sequence

from renaissance.impl.tree_sitter.adapter import TreeSitterAdapter
from renaissance.impl.tree_sitter.lst import LSTNode
from renaissance.utils.ast_utils import replace_dollar


class TreeSitterPatternFactory:
    def __init__(self, adapter: TreeSitterAdapter, language: str = "python"):
        self.adapter = adapter
        self.language = language

    def create(self, text: str) -> LSTNode:
        text = replace_dollar(text)
        if isinstance(self.adapter, TreeSitterAdapter):
            tree = self.adapter.parse_code(text)
            return self.adapter.to_lst(text, tree).root
        else:
            return self.adapter.to_lst(text).root

    def create_statements(self, text: str) -> Sequence[LSTNode]:
        return self.create(text).children

    def create_statement(self, text: str) -> LSTNode:
        return self.create_statements(text)[-1]

    def create_expression(self, text: str) -> LSTNode:
        return self.create_statement(text).children[-1]

from typing import Sequence

from renaissance.impl.tree_sitter_adapter.tree_sitter_adapter import TreeSitterAdapter
from renaissance.lst.lst import LSTNode, LST
from renaissance.utils.node_util import replace_dollar

SHOW_NODE = False


class TsPatternFactory:

    def __init__(self, adapter: TreeSitterAdapter, language: str = "python"):
        self.adapter = adapter
        self.language = language

    def create(self, text: str) -> LST:
        return self.adapter.to_lst(text, self.adapter.parse_code(text))

    def create_python_pattern(self, text: str) -> LSTNode:
        text = replace_dollar(text)
        return self.create(text).root

    def create_statements(self, text: str) -> Sequence[LSTNode]:
        return self.create_python_pattern(text).children

    def create_statement(self, text: str) -> LSTNode:
        return self.create_statements(text)[-1]

    def create_expression(self, text: str) -> LSTNode:
        return self.create_statement(text).children[-1]

"""AI: Factory for building tree-sitter AST patterns from text."""

from collections.abc import Sequence

from renaissance.integrations.tree_sitter.adapter import TreeSitterAdapter
from renaissance.integrations.tree_sitter.lst import LSTNode
from renaissance.utils.ast_utils import replace_dollar


class TreeSitterPatternFactory:
    """AI: Factory for building tree-sitter AST patterns from text."""

    def __init__(self, adapter: TreeSitterAdapter, language: str = "python"):
        """AI: Prepare a pattern factory for creating tree-sitter AST patterns from text."""
        self.adapter = adapter
        self.language = language

    def create(self, text: str) -> LSTNode:
        """AI: Parse text with tree-sitter and return the root node of the resulting LST."""
        text = replace_dollar(text)
        if isinstance(self.adapter, TreeSitterAdapter):
            tree = self.adapter.parse_code(text)
            return self.adapter.to_lst(text, tree).root
        return self.adapter.to_lst(text).root

    def create_statements(self, text: str) -> Sequence[LSTNode]:
        """AI: Parse text and return its top-level statement nodes."""
        return self.create(text).children

    def create_statement(self, text: str) -> LSTNode:
        """AI: Parse text and return its last top-level statement node."""
        return self.create_statements(text)[-1]

    def create_expression(self, text: str) -> LSTNode:
        """AI: Parse text and return the last expression node of its last statement."""
        return self.create_statement(text).children[-1]

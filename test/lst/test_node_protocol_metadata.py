"""Tests that tree-sitter LST nodes expose the expected NodeProtocol metadata."""

import tree_sitter_python

from renaissance.integrations.tree_sitter.adapter import TreeSitterAdapter
from renaissance.syntax_tree.semantic_kind import SemanticKind


def test_tree_sitter_nodes_expose_protocol_metadata():
    """AI: Assert a tree-sitter LST node exposes the expected parser_kind and semantic_kind."""
    adapter = TreeSitterAdapter(tree_sitter_python)
    root = adapter.to_lst("def f():\n    return 1\n", adapter.parse_code("def f():\n    return 1\n")).root

    assert root.parser_kind == "module"
    assert root.semantic_kind is SemanticKind.TRANSLATION_UNIT
    assert root.children[0].parser_kind == "function_definition"
    assert root.children[0].semantic_kind is SemanticKind.FUNCTION


def test_tree_sitter_kind_key_preserves_unknown_parser_identity():
    """AI: Assert kind_key falls back to the semantic kind for unmapped tree-sitter parser kinds."""
    adapter = TreeSitterAdapter(tree_sitter_python)
    parsed = adapter.parse_code("x = 1\n")
    root = adapter.to_lst("x = 1\n", parsed).root

    assert root.kind_key is SemanticKind.TRANSLATION_UNIT
    assert root.children[0].kind_key is SemanticKind.EXPRESSION

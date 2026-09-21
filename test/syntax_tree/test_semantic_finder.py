"""Tests for finding AST nodes by semantic kind via the ast_finder module."""

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree.ast_finder import find_semantic_kind
from renaissance.syntax_tree.semantic_kind import SemanticKind


def test_find_semantic_kind_uses_protocol_metadata():
    """AI: Assert find_semantic_kind locates nodes by their semantic kind via protocol metadata."""
    root = PythonRstNode.load_from_text("def f():\n    return 1\n")

    functions = find_semantic_kind(root, SemanticKind.FUNCTION)
    returns = find_semantic_kind(root, SemanticKind.RETURN)

    assert len(functions) == 1
    assert len(returns) == 1

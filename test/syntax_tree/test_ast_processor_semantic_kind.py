"""Tests that ASTProcessor finds nodes by semantic kind."""

from renaissance.integrations.python.ast.factory import PythonFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree.ast_processor import ASTProcessor
from renaissance.syntax_tree.semantic_kind import SemanticKind


def test_ast_processor_finds_nodes_by_semantic_kind():
    """AI: Assert ASTProcessor.find_semantic_kind locates nodes by their semantic kind."""
    root = PythonRstNode.load_from_text("def f():\n    return 1\n")
    processor = ASTProcessor(root, PythonFactory(PythonRstNode), in_memory=True)

    assert len(processor.find_semantic_kind(SemanticKind.FUNCTION)) == 1
    assert len(processor.find_semantic_kind(SemanticKind.RETURN)) == 1

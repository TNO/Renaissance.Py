"""Tests that the native ast-based Python node exposes the expected NodeProtocol metadata."""

import ast

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.integrations.python.ast.factory import PythonFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree.semantic_kind import SemanticKind


def test_native_ast_exposes_protocol_metadata():
    """AI: Assert a native ast-based Python node exposes the expected parser_kind and semantic_kind."""
    node = PythonFactory(ast.AST).create_from_text("def f(): pass").body[0]

    assert node.parser_kind == "FunctionDef"
    assert node.semantic_kind is SemanticKind.FUNCTION


def test_python_cst_exposes_protocol_metadata():
    """AI: Assert a Python CST node exposes the expected parser_kind and semantic_kind."""
    root = PythonCstNode.load_from_text("def f(): pass")

    assert root.parser_kind == "Module"
    assert root.semantic_kind is SemanticKind.TRANSLATION_UNIT
    assert root.children[0].semantic_kind is SemanticKind.FUNCTION


def test_python_rst_exposes_protocol_metadata():
    """AI: Assert a Python RST node exposes the expected parser_kind and semantic_kind."""
    root = PythonRstNode.load_from_text("f(1)")

    assert root.parser_kind == "Module"
    assert root.semantic_kind is SemanticKind.TRANSLATION_UNIT


def test_python_rst_kind_key_preserves_unknown_parser_identity():
    """AI: Assert kind_key falls back to the parser kind for an RST node with no mapped semantic kind."""
    root = PythonRstNode(ast.parse("match value:\n    case _:\n        pass\n").body[0])

    assert root.kind_key == "Match"

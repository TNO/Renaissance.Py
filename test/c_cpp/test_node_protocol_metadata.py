"""Tests that Clang JSON AST nodes expose the expected NodeProtocol metadata."""

from pathlib import Path

from renaissance.integrations.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.integrations.clang.cpp_utils import is_clang_kind
from renaissance.integrations.clang.kinds import CLANG_KIND_MAP
from renaissance.syntax_tree.semantic_kind import SemanticKind


def test_clang_json_nodes_expose_protocol_metadata():
    """AI: Assert a Clang JSON AST node exposes the expected parser_kind and semantic_kind."""
    node = ClangJsonASTNode.load_from_text("int f() { return 1; }", "test.c", [], Path())

    assert node.parser_kind == "TranslationUnitDecl"
    assert node.semantic_kind is SemanticKind.TRANSLATION_UNIT


def test_clang_common_kinds_map_to_shared_semantic_kinds():
    """AI: Assert common clang parser kinds map to their expected shared semantic kinds."""
    assert CLANG_KIND_MAP["FunctionDecl"] is SemanticKind.FUNCTION
    assert CLANG_KIND_MAP["CallExpr"] is SemanticKind.CALL
    assert CLANG_KIND_MAP["VarDecl"] is SemanticKind.DECLARATION
    assert CLANG_KIND_MAP["CXXRecordDecl"] is SemanticKind.CLASS


def test_clang_specific_unknown_kinds_keep_parser_identity():
    """AI: Assert an unmapped clang parser kind falls back to the generic NODE semantic kind."""
    parser_kind = "FriendDecl"

    assert parser_kind not in CLANG_KIND_MAP
    assert CLANG_KIND_MAP.get(parser_kind, SemanticKind.NODE) is SemanticKind.NODE


def test_clang_parser_kind_predicate_preserves_specific_concepts():
    """AI: Assert is_clang_kind matches only the exact requested parser kind."""
    node = type("Node", (), {"parser_kind": "CXXConstructorDecl"})()

    assert is_clang_kind(node, "CXXConstructorDecl")
    assert not is_clang_kind(node, "FunctionDecl")

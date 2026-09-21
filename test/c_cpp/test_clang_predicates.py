"""Tests for the Clang AST node kind predicate helpers."""

from renaissance.integrations.clang.predicates import (
    is_clang_compound_statement,
    is_clang_constructor,
    is_clang_declaration_reference,
    is_clang_macro_definition,
    is_clang_method,
    is_clang_type_reference,
)
from renaissance.syntax_tree.semantic_kind import SemanticKind


class Node:
    """AI: Build a minimal stand-in node for exercising clang predicate functions."""

    def __init__(self, parser_kind: str, semantic_kind: SemanticKind = SemanticKind.NODE):
        """AI: Store the parser-reported kind string and semantic kind for this stand-in node."""
        self.parser_kind = parser_kind
        self.semantic_kind = semantic_kind


def test_clang_parser_predicates_cover_native_and_json_spellings():
    """AI: Assert clang predicates recognize both native cursor-kind and clang_json spellings."""
    assert is_clang_type_reference(Node("TypeRef"))
    assert is_clang_type_reference(Node("TYPE_REF"))
    assert is_clang_type_reference(Node("type_identifier"))
    assert is_clang_declaration_reference(Node("DeclRefExpr"))
    assert is_clang_declaration_reference(Node("DECL_REF_EXPR"))
    assert is_clang_compound_statement(Node("CompoundStmt"))
    assert is_clang_compound_statement(Node("COMPOUND_STMT"))
    assert is_clang_method(Node("CXXMethodDecl"))
    assert is_clang_method(Node("CXX_METHOD"))
    assert is_clang_constructor(Node("CXXConstructorDecl"))
    assert is_clang_constructor(Node("CXX_CONSTRUCTOR"))


def test_clang_macro_and_semantic_predicates_are_explicit():
    """AI: Assert macro-definition predicates and semantic-kind defaults behave as expected."""
    assert is_clang_macro_definition(Node("MacroDefinition"))
    assert is_clang_macro_definition(Node("MACRO_DEFINITION"))
    assert Node("FunctionDecl", SemanticKind.FUNCTION).semantic_kind is SemanticKind.FUNCTION
    assert Node("FunctionDecl").semantic_kind is SemanticKind.NODE

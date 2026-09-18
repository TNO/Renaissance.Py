"""AI: Predicate helpers for identifying specific Clang AST node kinds."""

from renaissance.syntax_tree.node_protocol import NodeProtocol

TYPE_REFERENCE_KINDS = frozenset({"TypeRef", "TYPE_REF", "type_identifier"})
DECLARATION_REFERENCE_KINDS = frozenset({"DeclRefExpr", "DECL_REF_EXPR"})
COMPOUND_STATEMENT_KINDS = frozenset({"CompoundStmt", "COMPOUND_STMT"})
MACRO_DEFINITION_KINDS = frozenset({"MacroDefinition", "MACRO_DEFINITION"})
METHOD_KINDS = frozenset({"CXXMethodDecl", "CXX_METHOD"})
CONSTRUCTOR_KINDS = frozenset({"CXXConstructorDecl", "CXX_CONSTRUCTOR"})


def is_clang_kind(node: NodeProtocol, *parser_kinds: str) -> bool:
    """AI: Return True if node's parser_kind matches one of the given kind strings."""
    return node.parser_kind in parser_kinds


def is_clang_type_reference(node: NodeProtocol) -> bool:
    """AI: Return True if node is a Clang type-reference node."""
    return node.parser_kind in TYPE_REFERENCE_KINDS


def is_clang_declaration_reference(node: NodeProtocol) -> bool:
    """AI: Return True if node is a Clang declaration-reference node."""
    return node.parser_kind in DECLARATION_REFERENCE_KINDS


def is_clang_compound_statement(node: NodeProtocol) -> bool:
    """AI: Return True if node is a Clang compound statement (block)."""
    return node.parser_kind in COMPOUND_STATEMENT_KINDS


def is_clang_macro_definition(node: NodeProtocol) -> bool:
    """AI: Return True if node is a Clang macro definition."""
    return node.parser_kind in MACRO_DEFINITION_KINDS


def is_clang_method(node: NodeProtocol) -> bool:
    """AI: Return True if node is a Clang C++ method declaration."""
    return node.parser_kind in METHOD_KINDS


def is_clang_constructor(node: NodeProtocol) -> bool:
    """AI: Return True if node is a Clang C++ constructor declaration."""
    return node.parser_kind in CONSTRUCTOR_KINDS

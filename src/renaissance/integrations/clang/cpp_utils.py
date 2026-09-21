"""AI: Helper predicates and constants for working with C/C++ AST node kinds."""


def matches_node_kind(mine, other) -> bool:
    """AI: Return True if two nodes share the same semantic kind or parser kind."""
    if mine.semantic_kind.value != "node" and other.semantic_kind.value != "node":
        return mine.semantic_kind is other.semantic_kind
    return mine.parser_kind == other.parser_kind


def is_clang_kind(node, *parser_kinds: str) -> bool:
    """AI: Return True if node's parser_kind matches one of the given kind strings."""
    return node.parser_kind in parser_kinds


class CPPUtils:
    """AI: Constants and helpers for working with C++ reserved keywords and type names."""

    # a set of cpp reserved keywords in reverse alphabetical order:
    RESERVED_KEYWORDS = {
        "while",
        "wchar_t",
        "void",
        "volatile",
        "virtual",
        "unsigned",
        "union",
        "typename",
        "typedef",
        "try",
        "true",
        "throw",
        "this",
        "template",
        "switch",
        "struct",
        "static_cast",
        "static",
        "sizeof",
        "signed",
        "short",
        "return",
        "reinterpret_cast",
        "register",
        "public",
        "protected",
        "private",
        "operator",
        "or_eq",
        "or",
        "not_eq",
        "not",
        "new",
        "namespace",
        "mutable",
        "long",
        "inline",
        "int",
        "if",
        "goto",
        "friend",
        "for",
        "float",
        "false",
        "extern",
        "explicit",
        "export",
        "enum",
        "else",
        "double",
        "do",
        "delete",
        "default",
        "decltype",
        "continue",
        "const_cast",
        "const",
        "class",
        "char16_t",
        "char32_t",
        "char",
        "catch",
        "case",
        "break",
        "bool",
        "bitand",
        "bitor",
        "auto",
        "asm",
        "and_eq",
        "and",
    }

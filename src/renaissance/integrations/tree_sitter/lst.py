"""AI: Lossless syntax tree (LST) node implementation backed by tree-sitter."""

import sys
from typing import Any, Self, cast

from renaissance.integrations.tree_sitter.kinds import TREE_SITTER_KIND_MAP
from renaissance.syntax_tree.semantic_kind import SemanticKind
from renaissance.utils.ast_utils import format_node, match_children, match_props, next_sibling, preceding_sibling

IRRELEVANT_PROPS = {"source_code", "end_point", "start_point", "location", "type"}
IRRELEVANT_NODE = {"comment"}


class LSTNode:
    """AI: Lossless syntax tree (LST) node implementation backed by tree-sitter."""

    def __init__(
        self,
        node_type: str,
        properties: dict[str, Any],
        signature: str,
        offset: int = 0,
        children: list[Self] | None = None,
        parent: Self | None = None,
        root: Self | None = None,
    ):
        """AI: Wrap a tree-sitter node as a language-syntax-tree node with derived semantic kind."""
        self.root = root or self
        self.parent = parent
        self.children = [] if children is None else children
        self.properties = properties
        if node_type == "string" and signature.startswith("f"):
            node_type = "FormattedString"

        self.parser_kind = node_type
        self.semantic_kind = TREE_SITTER_KIND_MAP.get(node_type, SemanticKind.NODE)

        self.is_implicit = True
        self.show_props = False
        self.indent = ""

        self.is_statement = node_type == "Expr"
        self.referenced_by = []
        self.references = []

        self.signature = signature
        self.text = signature
        self.filename = "unknown"
        self.length = len(signature)
        self.offset = offset
        self.end_offset = self.offset + self.length
        self.extended_end_offset = self.end_offset

    @property
    def kind_key(self) -> SemanticKind | str:
        """AI: Return the semantic kind, or the raw parser kind when no semantic kind applies."""
        return self.semantic_kind if self.semantic_kind is not SemanticKind.NODE else self.parser_kind

    def __eq__(self, other):
        """AI: Return whether this node is structurally equal to `other`, ignoring irrelevant properties/children."""
        return (
            isinstance(other, type(self))
            and self.kind_key == other.kind_key
            and match_props(self.properties, other.properties, IRRELEVANT_PROPS)
            and match_children(self.children, other.children, IRRELEVANT_NODE)
        )

    def __hash__(self):
        """AI: Return a hash based on the node's kind key, properties, and children."""
        return hash((self.kind_key, frozenset(self.properties.items()), tuple(self.children)))

    def match_props(self, properties) -> bool:
        """AI: Return whether this node's properties match the given properties, ignoring irrelevant ones."""
        all_keys = (self.properties.keys() | properties.keys()) - IRRELEVANT_PROPS
        return all(self.properties.get(n) == properties.get(n) for n in all_keys)

    def match_children(self, children):
        """AI: Return whether this node's children match the given children at each corresponding index."""
        return all(i < len(self.children) and self.children[i] == child for i, child in enumerate(children))

    def add_child(self, child):  # LSTNode):
        """AI: Append child to this node's children and set its parent to this node."""
        self.children.append(child)
        child.parent = self

    @property
    def preceding_sibling(self) -> Self | None:
        """AI: Return the sibling node immediately preceding this one, or None."""
        return preceding_sibling(self)

    @property
    def next_sibling(self) -> Self | None:
        """AI: Return the sibling node immediately following this one, or None."""
        return next_sibling(self)

    @property
    def name(self) -> str:
        """AI: Return this node's "name" property, or an empty string if absent."""
        return self.properties.get("name", "")

    def binary_file_content(self):
        """AI: Return this node's source code encoded as bytes using the filesystem encoding."""
        src = cast("str", self.properties.get("source_code"))
        return src.encode(sys.getfilesystemencoding())

    @property
    def node(self):
        """AI: Return this node itself."""
        return self

    def __repr__(self):
        """AI: Return the formatted node representation."""
        return format_node(self)
        # raw_lines = self.signature.splitlines()
        # properties_text = "" if not self.show_props else self.properties
        # prefix = " " if len(raw_lines) < 2 else f"\n    {self.indent}"
        # formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
        # return (
        #     f"{self.indent}({self.kind}, {self.name},"
        #     f" {self.filename}[{self.offset}:{self.offset + self.length}])"
        #     f"{properties_text}:{''.join(formatted_lines)}\n"
        # )

    def is_part_of_translation_unit(self):
        """AI: Return whether this node belongs to a translation unit (has a root)."""
        return self.root is not None


class LST:
    """AI: Hold the root node of a language-syntax tree."""

    def __init__(self, root: LSTNode):
        """AI: Hold the root node of a language-syntax tree."""
        self.root = root

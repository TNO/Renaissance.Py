import sys
from typing import Any, Self, cast

from renaissance.utils.ast_utils import preceding_sibling, next_sibling, match_props, match_children

IRRELEVANT_PROPS = {"source_code", "end_point", "start_point", "location", "type"}
IRRELEVANT_NODE = {"comment"}

class LSTNode:
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

        self.root = root if root else self
        self.parent = parent
        self.children = [] if children is None else children
        self.properties = properties
        self.kind = node_type

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

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self.kind == other.kind
            and match_props(self.properties, other.properties, IRRELEVANT_PROPS)
            and match_children(self.children, other.children, IRRELEVANT_NODE)
        )

    def __hash__(self):
        return hash((self.kind, frozenset(self.properties.items()), tuple(self.children)))

    def match_props(self, properties) -> bool:
        all_keys = (self.properties.keys() | properties.keys()) - IRRELEVANT_PROPS
        return all(self.properties.get(n) == properties.get(n) for n in all_keys)

    def match_children(self, children):
        return all(i < len(self.children) and self.children[i] == child for i, child in enumerate(children))

    def add_child(self, child):  # LSTNode):
        self.children.append(child)
        child.parent = self

    @property
    def preceding_sibling(self) -> Self | None:
        return preceding_sibling(self)

    @property
    def next_sibling(self) -> Self | None:
        return next_sibling(self)

    @property
    def name(self) -> str:
        return self.properties.get("name", "")

    def binary_file_content(self):
        src = cast(str, self.properties.get("source_code"))
        return src.encode(sys.getfilesystemencoding())

    @property
    def node(self):
        return self

    def __str__(self):
        raw_lines = self.signature.splitlines()
        properties_text = "" if not self.show_props else self.properties
        prefix = " " if len(raw_lines) < 2 else f"\n    {self.indent}"
        formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
        return (
            f"{self.indent}({self.kind}, {self.name},"
            f" {self.filename}[{self.offset}:{self.offset + self.length}])"
            f"{properties_text}:{''.join(formatted_lines)}\n"
        )

    def is_part_of_translation_unit(self):
        return self.root is not None


class LST:
    def __init__(self, root: LSTNode):
        self.root = root

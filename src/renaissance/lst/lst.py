from typing import Any, Self


class LSTNode:
    def __init__(
            self,
            node_type: str,
            properties: dict[str, Any],
            signature: str,
            offset: int | None = None,
            children: list[Self] | None = None,
            parent: Self | None = None,
    ):
        self.kind = node_type
        self.properties = properties
        self.signature = signature
        self.offset = offset
        self.children = [] if children is None else children
        self.parent = parent
        self.show_props = False
        self.indent = ''
        self.length = len(signature)
        self.end_offset = self.offset + self.length
        self.is_statement = node_type == 'Expr'
        self.referenced_by = []
        self.references = []

    def add_child(self, child):  # LSTNode):
        self.children.append(child)
        child.parent = self

    @property
    def name(self):
        return self.properties.get('name')

    def __str__(self):
        raw_lines = self.signature.splitlines()
        properties_text = '' if not self.show_props else self.properties
        prefix = " " if len(raw_lines) < 2 else f"\n    {self.indent}"
        formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
        return (f"{self.indent}({self.kind}, {self.name},"
                f" {self.filename}[{self.offset}:{self.offset + self.length}])"
                f"{properties_text}:{''.join(formatted_lines)}\n")

    def is_part_of_translation_unit(self):
        return True


class LST:
    def __init__(self, root: LSTNode):
        self.root = root

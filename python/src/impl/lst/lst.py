from typing import Any, Dict, Generator, List, Optional



class LSTNode:
    def __init__(
        self,
        node_type: str,
        properties: Dict[str, Any],
        signature: str,
        offset: Optional[int] = None,
        children: Optional[List['LSTNode']] = None,
        parent: Optional['LSTNode'] = None,
    ):
        self.kind = node_type
        self.properties = properties
        self.signature = signature
        self.offset = offset
        self.children = children if children else []
        self.parent = parent
        self.show_props=False
        self.indent =''
        self.length = len(signature)

    def add_child(self, child): # LSTNode):
        self.children.append(child)
        child.parent = self

    @property
    def name(self):
        return self.properties['name'] if 'name' in self.properties else None

    @property
    def filename(self):
        return self.properties['name'] if 'name' in self.properties else None
    # def __repr__(self) -> str:
    #     return (
    #         f"LSTNode(type={self.kind}, sig={self.signature[:30]!r}, "
    #         f"offset={self.offset}, children={len(self.children)})"
    #     )

    def __repr__(self):
        raw_lines = self.signature.splitlines()
        properties_text = '' if not self.show_props else self.properties
        prefix = " " if len(raw_lines) < 2 else f"\n    {self.indent}"
        formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
        return f"{self.indent}({self.kind}, {self.name}, {self.filename}[{self.offset}:{self.offset + self.length}]){properties_text}:{''.join(formatted_lines)}\n"

    def is_part_of_translation_unit(self):
        return True

class LST:
    def __init__(self, root: LSTNode):
        self.root = root

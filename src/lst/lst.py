from typing import Any, Dict, List, Optional


class LSTNode:
    def __init__(
        self,
        node_type: str,
        attributes: Dict[str, Any],
        signature: str,
        offset: Optional[int] = None,
        children: Optional[List["LSTNode"]] = None,
        parent: Optional["LSTNode"] = None
    ):
        self.node_type = node_type
        self.attributes = attributes
        self.signature = signature
        self.offset = offset
        self.children = children if children else []
        self.parent = parent

    def add_child(self, child: "LSTNode"):
        self.children.append(child)
        child.parent = self

    def __repr__(self) -> str:
        return (
            f"LSTNode(type={self.node_type}, sig={self.signature[:30]!r}, "
            f"offset={self.offset}, children={len(self.children)})"
        )


class LST:
    def __init__(self, root: LSTNode):
        self.root = root

    def traverse(self):
        yield from self._traverse_recursive(self.root)

    def _traverse_recursive(self, node: LSTNode):
        yield node
        for child in node.children:
            yield from self._traverse_recursive(child)

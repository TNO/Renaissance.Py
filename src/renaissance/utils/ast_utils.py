from pathlib import Path
from collections import deque
from typing import Tuple

from renaissance.impl import MATCH_ALL, MATCH_ONE


def replace_dollar(text: str) -> str:
    return text.replace("$$", MATCH_ALL).replace("$", MATCH_ONE)


def use_dollar(text: str) -> str:
    return text.replace(MATCH_ALL, "$$").replace(MATCH_ONE, "$")


def detect_placeholder(signature: str, original_node_type: str) -> Tuple[bool, str, str]:
    """
    Detect if the given signature represents a placeholder symbol.

    Returns:
        (is_placeholder, coerced_node_type, placeholder_name_or_signature)
    """
    if not signature:
        return False, original_node_type, ""
    if (
        (signature.startswith(MATCH_ALL) or signature.startswith("$$")) and " " not in signature and "(" not in signature
    ):  # legacy compatibility
        return True, MATCH_ALL, signature
    elif (signature.startswith(MATCH_ONE) or signature.startswith("$")) and " " not in signature and "(" not in signature:
        return True, MATCH_ONE, signature
    return False, original_node_type, "-"


# duplicate of ast node process
def traverse(node):
    todo = deque([node])
    while todo:
        node = todo.popleft()
        if hasattr(node, "children"):
            todo.extend(node.children)
        yield node


def process_node(node, action) -> None:
    action(node)
    if node.children:
        for child in node.children:
            process_node(child, action)


def preceding_sibling(node):
    parent = node.parent
    if not parent:
        return None
    siblings = parent.children
    index = siblings.index(node)
    return siblings[index - 1] if index > 0 else None


def next_sibling(self):
    parent = self.parent
    if not parent:
        return None
    siblings = parent.children
    index = siblings.index(self)
    return siblings[index + 1] if index < len(siblings) - 1 else None


def match_props(mine, other, irrelevant_props) -> bool:
    all_keys = (mine.keys() | other.keys()) - irrelevant_props
    return all(mine.get(n) == other.get(n) for n in all_keys)


def match_children(mine, other, irrelevant_kinds):
    if mine == None or other == None:
        return mine == other
    return all((i < len(mine) and mine[i] == child) or child.ast_type.__name__ in irrelevant_kinds for i, child in enumerate(other))


def format_node(node):
    raw_lines = node.signature.splitlines()
    properties_text = "" if not node.show_props else node.properties
    prefix = " " if len(raw_lines) < 2 else f"\n    {node.indent}"
    formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
    return f"{node.indent}({node.ast_type.__name__}, {node.name}, {node.filename}[{node.offset}:{node.offset + node.length}]){properties_text}:{''.join(formatted_lines)}\n"

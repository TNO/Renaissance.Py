from collections import deque

from renaissance.integrations import MATCH_ALL, MATCH_ONE


def replace_dollar(text: str) -> str:
    """Replace dollar-sign placeholders in the given text with their corresponding match symbols.

    Two literal dollar-sign characters (`$$`) are replaced with MATCH_ALL; a single literal dollar-sign
    character (`$`) is replaced with MATCH_ONE.
    """
    return text.replace("$$", MATCH_ALL).replace("$", MATCH_ONE)


def use_dollar(text: str) -> str:
    """Replace match symbols in the given text with their corresponding dollar-sign placeholders.

    MATCH_ALL is replaced with two literal dollar-sign characters (`$$`); MATCH_ONE is replaced with a
    single literal dollar-sign character (`$`).
    """
    return text.replace(MATCH_ALL, "$$").replace(MATCH_ONE, "$")


def detect_placeholder(signature: str, original_node_type: str) -> tuple[bool, str, str]:
    """Detect if the given signature represents a placeholder symbol.

    Returns:
        (is_placeholder, coerced_node_type, placeholder_name_or_signature)

    """
    if not signature:
        return False, original_node_type, ""
    if signature.startswith((MATCH_ALL, "$$")) and " " not in signature and "(" not in signature:
        # legacy compatibility
        return True, MATCH_ALL, signature
    if signature.startswith((MATCH_ONE, "$")) and " " not in signature and "(" not in signature:
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
    preceding_index = siblings.index(node) - 1
    return siblings[preceding_index] if preceding_index >= 0 else None


def next_sibling(self):
    parent = self.parent
    if not parent:
        return None
    siblings = parent.children
    next_index = siblings.index(self) + 1
    return siblings[next_index] if next_index < len(siblings) else None


def match_props(mine, other, irrelevant_props) -> bool:
    all_keys = (mine.keys() | other.keys()) - irrelevant_props
    return all(mine.get(n) == other.get(n) for n in all_keys)


def match_children(mine, other, irrelevant_kinds) -> bool:
    if mine is None or other is None:
        return mine == other
    return all((i < len(mine) and mine[i] == child) or child.ast_type.__name__ in irrelevant_kinds for i, child in enumerate(other))


def format_node(node) -> str:
    raw_lines = node.signature.splitlines()
    properties_text = "" if not node.show_props else node.properties
    prefix = " " if len(raw_lines) < 2 else f"\n    {node.indent}"
    formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
    return (
        f"{node.indent}({node.ast_type.__name__}, {node.name}, "
        f"{node.filename}[{node.offset}:{node.offset + node.length}])"
        f"{properties_text}:{''.join(formatted_lines)}\n"
    )

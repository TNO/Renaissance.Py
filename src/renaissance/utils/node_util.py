# python/src/utils/node_util.py
from collections import deque
from typing import Tuple

from renaissance.impl import MATCH_ALL, MATCH_ONE


def replace_dollar(text: str) -> str:
    return text.replace('$$', MATCH_ALL).replace('$', MATCH_ONE)


def detect_placeholder(
    signature: str, original_node_type: str
) -> Tuple[bool, str, str]:
    """
    Detect if the given signature represents a placeholder symbol.

    Returns:
        (is_placeholder, coerced_node_type, placeholder_name_or_signature)
    """
    if not signature:
        return (False, original_node_type, "")
    if (signature.startswith(MATCH_ALL) or signature.startswith("$$") ) and ' ' not in signature:  # legacy compatibility
        return (True, MATCH_ALL, signature)
    elif (signature.startswith(MATCH_ONE) or signature.startswith("$")) and ' ' not in signature:
        return (True, MATCH_ONE, signature)
    return (False, original_node_type, "-")

def traverse(node):
    todo = deque([node])
    while todo:
        node = todo.popleft()
        todo.extend(node.children)
        yield node

def process_node(node, action ) -> None:
    action(node)
    if node.children:
        for child in node.children:
            process_node(child, action)

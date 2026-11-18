# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The display of a node, with which the core and the parser bindings implement __repr__."""

from renaissance.core.model.node_utils import DISPLAY_PARSER_KIND


def format_node(node) -> str:
    """AI: Return a human-readable, indented display string for a single AST node."""
    raw_lines = node.signature.splitlines()
    properties_text = "" if not node.show_props else node.properties
    prefix = " " if len(raw_lines) < 2 else f"\n    {node.indent}"
    formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
    semantic_name = node.semantic_kind.value
    kind = node.parser_kind if DISPLAY_PARSER_KIND.get() or semantic_name == "node" else semantic_name
    return (
        f"{node.indent}({kind}, {node.name}, "
        f"{node.filename}[{node.offset}:{node.offset + node.length}])"
        f"{properties_text}:{''.join(formatted_lines)}\n"
    )

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Helpers with which a parser binding implements node equality and node display."""

from renaissance.core.model.node_utils import DISPLAY_PARSER_KIND


def match_props(mine, other, irrelevant_props) -> bool:
    """AI: Return True if mine and other agree on all properties except the irrelevant ones."""
    all_keys = (mine.keys() | other.keys()) - irrelevant_props
    return all(mine.get(n) == other.get(n) for n in all_keys)


def match_children(mine, other, irrelevant_kinds) -> bool:
    """AI: Return True if every child in other matches the corresponding child in mine (or has an irrelevant kind)."""
    if mine is None or other is None:
        return mine == other
    # TODO(pjljvandelaar): asymmetric - extra trailing children of mine are ignored, so a == b need not imply b == a.
    #  https://github.com/TNO/Renaissance.Py/issues/187
    return all((i < len(mine) and mine[i] == child) or child.parser_kind in irrelevant_kinds for i, child in enumerate(other))


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

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Render a tree-sitter LST as a Mermaid graph for visualization."""

import re

from renaissance.integrations.tree_sitter.lst import LST


def signature_to_id(signature: str) -> str:
    """AI: Derive a short, filesystem/identifier-safe id from a node signature."""
    text = signature.replace("\n", " ")
    return re.sub(r"[^\w\s]", "", text)[:30]  # Remove punctuation, limit length


class LstVisualizer:
    """AI: Render a tree-sitter LST as a Mermaid graph for visualization."""

    def __init__(self) -> None:
        """AI: Prepare a visualizer that renders an LST as a Mermaid graph."""
        self.lines = ["graph TD"]
        self.counter = 0
        self.node_ids = {}

    def _get_node_id(self, node):
        if node not in self.node_ids:
            self.counter += 1
            self.node_ids[node] = f"n{self.counter}"
        return self.node_ids[node]

    def _render_node(self, node) -> None:
        node_id = self._get_node_id(node)
        label = f"""\
            {node_id}: {node.semantic_kind} ({node.parser_kind}) {{
            offset: {node.offset}
            signature: {signature_to_id(node.signature)}
            }}"""
        label = label.replace("\n", "<br>")
        self.lines.append(f'{node_id}["{label}"]')
        for child in node.children:
            self._render_node(child)
            child_id = self._get_node_id(child)
            self.lines.append(f"{node_id} --> {child_id}")

    def render(self, lst: LST):
        """AI: Render the given LST as a Mermaid graph diagram string."""
        self._render_node(lst.root)
        return "\n".join(self.lines)

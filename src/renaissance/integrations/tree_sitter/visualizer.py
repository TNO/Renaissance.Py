"""AI: Render a tree-sitter LST as a Mermaid graph for visualization."""

from renaissance.integrations.tree_sitter.lst import LST
from renaissance.utils.text_utils import signature_to_id


class LstVisualizer:
    """AI: Render a tree-sitter LST as a Mermaid graph for visualization."""

    def __init__(self):
        """AI: Prepare a visualizer that renders an LST as a Mermaid graph."""
        self.lines = ["graph TD"]
        self.counter = 0
        self.node_ids = {}

    def _get_node_id(self, node):
        if node not in self.node_ids:
            self.counter += 1
            self.node_ids[node] = f"n{self.counter}"
        return self.node_ids[node]

    def _render_node(self, node):
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

from renaissance.lst.lst import LST
import re

from renaissance.utils.text_utils import TextUtils


class LSTMermaidVisualizer:
    def __init__(self):
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
{node_id}: {node.kind} {{
offset: {node.offset}
signature: {TextUtils.clean_signature(node.signature)}
}}"""
        label = label.replace("\n", "<br>")
        self.lines.append(f'{node_id}["{label}"]')
        for child in node.children:
            self._render_node(child)
            child_id = self._get_node_id(child)
            self.lines.append(f"{node_id} --> {child_id}")

    def render(self, lst: LST):
        self._render_node(lst.root)
        return "\n".join(self.lines)


from renaissance.lst.lst import LST
import re


def _clean_signature(signature):
    text = signature.replace("\n", " ")
    return re.sub(r"[^\w\s]", "", text)[:30]  # Remove punctuation, limit length


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

    @staticmethod
    def _escape_label(text):
        return text.replace('"', '\\"').replace("\n", " ").strip()

    def _render_node(self, node):
        node_id = self._get_node_id(node)
        label = f"""\
{node_id}: {node.kind} {{
offset: {node.offset}
signature: {_clean_signature(node.signature)}
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

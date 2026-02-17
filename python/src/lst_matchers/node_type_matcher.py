from lst.lst import LSTNode

from typing import List

from syntax_tree import PatternMatch


class NodeTypeMatcher:
    """
    Matches all nodes in an LST that have a given node type.
    Mimics the interface of StructuralPatternMatcher.
    """

    def __init__(self, node_type: str):
        self.node_type = node_type

    def match(self, lst_root: LSTNode) -> List[PatternMatch]:
        results = []
        self._search(lst_root, results)
        return results

    def _search(self, node: LSTNode, results: List[PatternMatch]):
        if node.kind == self.node_type:
            match = PatternMatch()
            match.add_binding("match", node)
            results.append(match)
        for child in node.children:
            self._search(child, results)

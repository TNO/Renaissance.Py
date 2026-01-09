from lst.lst import LSTNode
from matchers.pattern_matcher import MatchResult
from typing import List


class NodeTypeMatcher:
    """
    Matches all nodes in an LST that have a given node type.
    Mimics the interface of StructuralPatternMatcher.
    """

    def __init__(self, node_type: str):
        self.node_type = node_type

    def match(self, lst_root: LSTNode) -> List[MatchResult]:
        results: List[MatchResult] = []
        self._search(lst_root, results)
        return results

    def _search(self, node: LSTNode, results: List[MatchResult]):
        if node.node_type == self.node_type:
            match = MatchResult()
            match.add_binding("match", node)
            results.append(match)
        for child in node.children:
            self._search(child, results)

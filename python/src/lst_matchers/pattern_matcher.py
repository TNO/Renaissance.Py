from lst.lst import LSTNode
from typing import Dict, List

from syntax_tree.ast_node import MATCH_ONE


class MatchResult:
    def __init__(self):
        self.bindings: Dict[str, List[LSTNode]] = {}

    def add_binding(self, placeholder: str, node: LSTNode):
        if placeholder not in self.bindings:
            self.bindings[placeholder] = []
        self.bindings[placeholder].append(node)

    def __repr__(self):
        return f"MatchResult(bindings={self.bindings})"


class StructuralPatternMatcher:
    def __init__(self, pattern_root: LSTNode):
        self.pattern_root = pattern_root

    def match(self, lst_root: LSTNode) -> List[MatchResult]:
        results = []
        self._search(lst_root, results)
        return results

    def _search(self, node: LSTNode, results: List[MatchResult]):
        match = self._match_nodes(self.pattern_root, node)
        if match:
            results.append(match)
        for child in node.children:
            self._search(child, results)

    def _match_nodes(self, pattern: LSTNode, target: LSTNode) -> MatchResult | None:
        result = MatchResult()

        def recurse(p_node: LSTNode, t_node: LSTNode) -> bool:
            if (p_node.kind == "identifier"
                or p_node.kind == "placeholder")and (
                p_node.signature.startswith(
                    "$"
                )  # this does not work for call expressions in tree sitter
                or 
                p_node.signature.startswith(MATCH_ONE)
            ):
                result.add_binding(p_node.signature[1:], t_node)
                return True
            if p_node.kind != t_node.kind:
                return False
            if len(p_node.children) != len(t_node.children):
                return False
            for p_child, t_child in zip(p_node.children, t_node.children):
                if not recurse(p_child, t_child):
                    return False
            return True

        return result if recurse(pattern, target) else None

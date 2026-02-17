from typing import Callable, TypeVar, Generic, List, Union, Tuple, Optional

from impl.tree_sitter_adapter.tree_sitter_adapter import TreeSitterAdapter
from syntax_tree import PatternMatch, MatchFinder

R = TypeVar("R")
MatchSource = Union[str, Tuple[str, str]]


class Match:
    pass


class PatternMatcherInterfaceExtended:
    def __init__(self, adapter: TreeSitterAdapter):
        self.adapter = adapter

    def match_pattern(self, code_base: str, pattern_code: str) -> List[PatternMatch]:
        base_tree = self.adapter.parse_code(code_base)
        lst = self.adapter.to_lst(code_base, base_tree)
        pattern_tree = self.adapter.to_lst(
            pattern_code, self.adapter.parse_code(pattern_code)
        ).root
        matcher = [] #StructuralPatternMatcher(pattern_tree)
        results = matcher.match(lst.root)


        return [PatternMatch(res) for res in results]

    def find_by_node_type(self, code_base: str, node_type: str) -> List[PatternMatch]:
        base_tree = self.adapter.parse_code(code_base)
        lst = self.adapter.to_lst(code_base, base_tree)

        matches = []
        for node in lst.traverse():
            if node.kind == node_type:
                mr = PatternMatch()
                mr.add_binding("match", node)
                matches.append(Match(mr))
        return matches


class Extractor(Generic[R]):
    def __init__(self, interface: PatternMatcherInterfaceExtended):
        self.interface = interface
        self.rules: List[
            Tuple[MatchSource, Callable[[Match], R], Optional[Callable[[Match], bool]]]
        ] = []

    def add_rule(
        self,
        source: MatchSource,
        extractor_fn: Callable[[Match], R] = lambda n: n,
        filter_fn: Optional[Callable[[Match], bool]] = None,
    ):
        self.rules.append((source, extractor_fn, filter_fn))

    def run(self, raw: str) -> List[R]:
        code  = self.interface.create_statements(raw)
        results: List[R] = []
        for txt, extract_fn, filter_fn in self.rules:
            pattern  = self.interface.create_statements(txt)
            matches = MatchFinder.match_pattern(code, pattern, {})
            for match in matches:
                try:
                    if filter_fn is None or filter_fn(match.nodes):
                        results.append(extract_fn(match))
                except Exception as e:
                    print(f"Warning: extractor failed on match {match}: {e}")
        return results

from typing import Callable, TypeVar, Generic, List, Union, Tuple, Optional
from matchers.match import Match
from matchers.pattern_matcher import StructuralPatternMatcher
from adapters.tree_sitter_adapter import TreeSitterAdapter

R = TypeVar("R")
MatchSource = Union[str, Tuple[str, str]]


class PatternMatcherInterfaceExtended:
    def __init__(self, adapter: TreeSitterAdapter):
        self.adapter = adapter

    def match_pattern(self, code_base: str, pattern_code: str) -> List[Match]:
        base_tree = self.adapter.parse_code(code_base)
        lst = self.adapter.to_lst(code_base, base_tree)
        pattern_tree = self.adapter.to_lst(
            pattern_code, self.adapter.parse_code(pattern_code)
        ).root
        matcher = StructuralPatternMatcher(pattern_tree)
        results = matcher.match(lst.root)
        from matchers.match import Match as M

        return [M(res) for res in results]

    def find_by_node_type(self, code_base: str, node_type: str) -> List[Match]:
        base_tree = self.adapter.parse_code(code_base)
        lst = self.adapter.to_lst(code_base, base_tree)
        from matchers.pattern_matcher import MatchResult
        from matchers.match import Match as M

        matches = []
        for node in lst.traverse():
            if node.node_type == node_type:
                mr = MatchResult()
                mr.add_binding("match", node)
                matches.append(M(mr))
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
        extractor_fn: Callable[[Match], R],
        filter_fn: Optional[Callable[[Match], bool]] = None,
    ):
        self.rules.append((source, extractor_fn, filter_fn))

    def run(self, code_base: str) -> List[R]:
        results: List[R] = []
        for source, extract_fn, filter_fn in self.rules:
            if isinstance(source, str):
                matches = self.interface.find_by_node_type(code_base, source)
            elif isinstance(source, tuple) and source[1] == "pattern":
                matches = self.interface.match_pattern(code_base, source[0])
            else:
                continue
            for match in matches:
                try:
                    if filter_fn is None or filter_fn(match):
                        results.append(extract_fn(match))
                except Exception as e:
                    print(f"Warning: extractor failed on match {match}: {e}")
        return results

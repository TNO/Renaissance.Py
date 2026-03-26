from renaissance.impl.tree_sitter_adapter.ts_pattern_factory import TsPatternFactory
from renaissance.syntax_tree import MatchFinder, PatternMatch


class Extractor:
    def __init__(self, factory: TsPatternFactory, patterns: list[str]):
        self.factory = factory
        self.patterns = patterns

    def run(self, raw: str) -> list[PatternMatch]:
        code = self.factory.create_statements(raw)
        results = []
        for rule in self.patterns:
            pattern = self.factory.create_statements(rule)
            results.extend(MatchFinder.match_pattern(code, pattern, {}))  # type: ignore[assignment]
        return results

from renaissance.impl.tree_sitter.pattern_factory import TsPatternFactory
from renaissance.syntax_tree import MatchFinder, PatternMatch
from renaissance.syntax_tree.match_finder import match_pattern


class Extractor:
    def __init__(self, factory: TsPatternFactory, patterns: list[str]):
        self.factory = factory
        self.patterns = patterns

    def run(self, raw: str) -> list[PatternMatch]:
        code = self.factory.create_statements(raw)
        results = []
        for rule in self.patterns:
            pattern = self.factory.create_statements(rule)
            results.extend(match_pattern(code, pattern, {}))
        return results

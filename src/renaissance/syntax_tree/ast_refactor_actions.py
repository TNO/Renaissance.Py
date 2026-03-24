from functools import cache
from typing import Callable, Optional, Sequence

from renaissance.impl.clang.c_pattern_factory import CPPPatternFactory
from .ast_finder import ASTFinder
from .ast_node import ASTNode
from .ast_processor import ASTProcessor
from .match_finder import MatchFinder, PatternMatch


class ASTRefactorActions:
    def __init__(self, processor: ASTProcessor, pattern_factory: CPPPatternFactory) -> None:
        self.processor = processor
        self.pattern_factory = pattern_factory
        self.replaced: set[int] = set()

    def replace_expr(self, name: str, replacement: str, kind: Optional[str] = None):
        def test(n: "ASTNode"):
            if (kind and ASTFinder.matches_kind(n, kind)) and n.name == name:
                yield n

        [self.processor.replace(found.text.replace(found.name, replacement, 1), found)
         for found in self.processor.find_all(test)]

    def replace_name(
        self,
        name: str,
        replacement: str,
        kind: Optional[str] = None,
        skip_kind: Optional[str] = None,
    ):
        matches_name: Callable[[Optional["ASTNode"]], bool] = (
            lambda n1: (not kind or ASTFinder.matches_kind(n1, kind))
            and (not skip_kind or not ASTFinder.matches_kind(n1, skip_kind))
            and n1
            and n1.name == name
        )
        found_nodes = self.processor.find_all(matches_name)
        [self.replaced.add(found.offset) for found in found_nodes if found.offset not in self.replaced]
        for n in found_nodes:
            self.processor.replace(n.text.replace(n.name, replacement, 1), n)

    def replace_text(
        self,
        text: str,
        replacement: str,
        kind: Optional[str] = None,
        skip_kind: Optional[str] = None,
    ):
        matches_text: Callable[[Optional["ASTNode"]], bool] = (
            lambda n: (not kind or ASTFinder.matches_kind(n, kind))
            and (not skip_kind or not ASTFinder.matches_kind(n, skip_kind))
            and n is not None and n.text == text
        )

        found_nodes = self.processor.find_all(matches_text)
        [self.replaced.add(found.offset) for found in found_nodes if found.offset not in self.replaced]

        [self.processor.replace(n.text.replace(n.name, replacement, 1), n) for n in found_nodes]

    def replace_declaration(self, declaration: str, replacement: str):
        for match in self.find_declaration(declaration):
            self.processor.replace(replacement, match)

    def _replace_patterns(
        self,
        node: ASTNode,
        replacement: str,
        patterns: Sequence[Sequence[ASTNode]],
        matches: Sequence[PatternMatch],
    ):
        if not patterns:
            self.processor.replace(replacement, matches)
            return
        [
            self._replace_patterns(m.nodes[0], replacement, patterns[1:], list(matches) + [m])
            for m in MatchFinder.find_all([node], patterns[0])
        ]

    @cache
    def find_declaration(self, decl_pattern: str):
        pattern = self.pattern_factory.create_declaration(decl_pattern)
        return self.processor.find_match(pattern)

    @cache
    def collect(self, pattern: str, pattern_kind: str):
        root = self.pattern_factory.create(pattern, pattern_kind)

        return self.processor.find_match(root)

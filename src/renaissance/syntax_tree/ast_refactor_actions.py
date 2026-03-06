from functools import cache
from typing import Callable, Optional, Sequence

from renaissance.common import Stream
from .match_finder import MatchFinder, PatternMatch

from renaissance.impl.clang.c_pattern_factory import CPPPatternFactory

from .ast_finder import ASTFinder
from .ast_processor import ASTProcessor
from .ast_node import ASTNode


class ASTRefactorActions:
    def __init__(
        self, processor: ASTProcessor, pattern_factory: CPPPatternFactory
    ) -> None:
        self.processor = processor
        self.pattern_factory = pattern_factory
        self.replaced: set[int] = set()

    def replace_expr(self, name: str, replacement: str, kind: Optional[str] = None):
        def test(n: "ASTNode"):
            if (kind and ASTFinder.matches_kind(n, kind)) and n.name == name:
                yield n

        self.processor.find_all(test).for_each(
            lambda n: self.processor.replace(
                n.text.replace(n.name, replacement, 1), n
            )
        )

    def replace_name(
        self,
        name: str,
        replacement: str,
        kind: Optional[str] = None,
        skip_kind: Optional[str] = None,
    ):
        matches_name: Callable[[Optional["ASTNode"]], bool] = (
            lambda n: (not kind or ASTFinder.matches_kind(n, kind))
                      and (not skip_kind or not ASTFinder.matches_kind(n, skip_kind))
                      and n.name == name        # TODO: prevent get_name on None
        )
        self.processor.find_all(matches_name).filter(
            lambda n: not n.offset in self.replaced
        ).action(lambda n: self.replaced.add(n.offset)).for_each(
            lambda n: self.processor.replace(
                n.text.replace(n.name, replacement, 1), n
            )
        )

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
                      and n.text == text      # TODO: prevent get_text on None
        )
        self.processor.find_all(matches_text).filter(
            lambda n: not n.offset in self.replaced
        ).action(lambda n: self.replaced.add(n.offset)).for_each(
            lambda n: self.processor.replace(replacement, n)
        )

    def replace_declaration(self, declaration: str, replacement: str):
        matches = self.find_declaration(declaration)
        Stream(matches).for_each(lambda m: self.processor.replace(replacement, m))

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
        MatchFinder.find_all([node], patterns[0]).for_each(
            lambda m: self._replace_patterns(
                m.nodes[0], replacement, patterns[1:], list(matches) + [m]
            )
        )

    @cache
    def find_declaration(self, decl_pattern: str):
        pattern = self.pattern_factory.create_declaration(decl_pattern)
        return self.processor.find_match(pattern).to_list()

    @cache
    def collect(self, pattern: str, pattern_kind: str):
        root = self.pattern_factory.create(pattern, pattern_kind)

        return self.processor.find_match(root).to_list()


import re
from typing import Callable, Iterator, Optional

from .ast_node import ASTNode
from renaissance.common import Stream


class ASTFinder:
    KIND_MATCH = re.compile(r'[\W_]+')

    @staticmethod
    def find_all(ast_node: ASTNode, function: Callable[[ASTNode], Iterator[ASTNode] | bool]) -> Stream[ASTNode]:
        return Stream(ASTFinder.__find_all(ast_node, function))

    @staticmethod
    def find_kind(ast_node: ASTNode, kind: str | re.Pattern[str]) -> Stream[ASTNode]:
        return Stream(ASTFinder.__matches_kind(ast_node, kind))

    @staticmethod
    def find(ast_node: ASTNode, kind: str | re.Pattern[str]) -> Stream[ASTNode]:
        return ASTFinder.__matches_kind(ast_node, kind)

    @staticmethod
    def matches_kind(ast_node: Optional[ASTNode], kind: str | re.Pattern[str]) -> bool:
        # compare kind with the ast_node kind only using word characters
        # get kind of the ast_node with only word characters
        if ast_node is None:
            return False
        ast_kind = ASTFinder.KIND_MATCH.sub('', ast_node.kind).lower()
        pattern = kind if isinstance(kind, re.Pattern) else re.compile(kind, re.IGNORECASE)
        return pattern.fullmatch(ast_kind) is not None

    @staticmethod
    def __find_all(ast_node: ASTNode, function: Callable[[ASTNode], Iterator[ASTNode] | bool]) -> Iterator[ASTNode]:
        result = function(ast_node)
        if isinstance(result, bool) and result:
            yield ast_node
        elif isinstance(result, Iterator):
            yield from result
        for child in ast_node.children:
            yield from ASTFinder.__find_all(child, function)

    @staticmethod
    def __matches_kind(ast_node: ASTNode, kind: str | re.Pattern[str]) -> Iterator[ASTNode]:
        pattern = kind if isinstance(kind, re.Pattern) else re.compile(kind, re.IGNORECASE)
        ast_kind = ASTFinder.KIND_MATCH.sub('', ast_node.kind).lower()

        if pattern.fullmatch(ast_kind):
            yield ast_node
        for child in ast_node.children:
            assert isinstance(child, type(ast_node)), f'Expected {type(ast_node)} but got {type(child)}'
            yield from ASTFinder.__matches_kind(child, pattern)
#
# class NodeTypeMatcher:
#     """
#     Matches all nodes in an LST that have a given node type.
#     Mimics the interface of StructuralPatternMatcher.
#     """
#
#     def __init__(self, node_type: str):
#         self.node_type = node_type
#
#     def match(self, lst_root: LSTNode) -> List[PatternMatch]:
#         results = []
#         self._search(lst_root, results)
#         return results
#
#     def _search(self, node: LSTNode, results: List[PatternMatch]):
#         if node.kind == self.node_type:
#             match = ("match", node)
#             results.append(match)
#         for child in node.children:
#             self._search(child, results)

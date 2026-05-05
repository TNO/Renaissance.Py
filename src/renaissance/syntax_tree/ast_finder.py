import re
from typing import Callable, Iterator, Optional, Sequence


from .ast_node import ASTNode


class ASTFinder:
    KIND_MATCH = re.compile(r"[\W_]+")

    @staticmethod
    def find_all(ast_node: ASTNode, function: Callable[[ASTNode], Iterator[ASTNode] | bool]) -> Sequence[ASTNode]:
        return list(ASTFinder.__find_all(ast_node, function))

    @staticmethod
    def find_kind(ast_node: ASTNode, kind: str | re.Pattern[str]) -> Sequence[ASTNode]:
        return list(ASTFinder.__matches_kind(ast_node, kind))

    @staticmethod
    def find(ast_node: ASTNode, kind: str | re.Pattern[str]) -> Sequence[ASTNode]:
        return list(ASTFinder.__matches_kind(ast_node, kind))

    @staticmethod
    def matches_kind(ast_node: Optional[ASTNode], kind: str | re.Pattern[str]) -> bool:
        # compare kind with the ast_node kind only using word characters
        # get kind of the ast_node with only word characters
        if ast_node is None:
            return False
        ast_kind = ASTFinder.KIND_MATCH.sub("", ast_node.kind).lower()
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
        node_kind = ast_node.kind if ast_node.kind else ""
        ast_kind = ASTFinder.KIND_MATCH.sub("", node_kind).lower()

        if pattern.fullmatch(ast_kind):
            yield ast_node
        for child in ast_node.children:
            # assert isinstance(child, type(ast_node)), f'Expected {type(ast_node)} but got {type(child)}'
            yield from ASTFinder.__matches_kind(child, pattern)


def find_kind(ast_node, kind: str) -> Sequence:
    return ASTFinder.find_kind(ast_node, kind)

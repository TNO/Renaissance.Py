import re
from typing import Callable, Iterator, TypeVar

from common import Stream
from .ast_node import ASTNode

ASTNodeType = TypeVar("ASTNodeType", bound='ASTNode')

class ASTFinder:
    @staticmethod
    def find_all(ast_node: ASTNodeType, function: Callable[[ASTNodeType], Iterator[ASTNodeType]])-> Stream[ASTNodeType]:
        return Stream(ASTFinder.__find_all(ast_node, function))

    @staticmethod
    def find_kind(ast_node: ASTNodeType, kind: str)-> Stream[ASTNodeType]:
        return Stream(ASTFinder.__find_kind(ast_node, kind))

    @staticmethod
    def __find_all(ast_node: ASTNodeType, function: Callable[[ASTNodeType], Iterator[ASTNodeType]])-> Iterator[ASTNodeType]:
        yield from function(ast_node)
        for child in ast_node.get_children():
            yield from ASTFinder.__find_all(child, function)

    @staticmethod
    def __find_kind(ast_node: ASTNodeType, kind: str)-> Iterator[ASTNodeType]:
        pattern = re.compile(kind)
        def match(target: ASTNodeType) -> Iterator[ASTNodeType]:
            if (pattern.match(target.get_kind())):
                yield target
        yield from ASTFinder.__find_all(ast_node, match)

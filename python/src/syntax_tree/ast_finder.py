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
        return Stream(ASTFinder.__matches_kind(ast_node, kind))

    @staticmethod
    def matches_kind(ast_node: ASTNode, kind: str)-> bool:
        pattern = re.compile(kind)
        return pattern.match(ast_node.get_kind())!=None

    @staticmethod
    def __find_all(ast_node: ASTNodeType, function: Callable[[ASTNodeType], Iterator[ASTNodeType]])-> Iterator[ASTNodeType]:
        yield from function(ast_node)
        for child in ast_node.get_children():
            yield from ASTFinder.__find_all(child, function)

    @staticmethod
    def __matches_kind(ast_node: ASTNodeType, kind:str)-> Iterator[ASTNodeType]:
        pattern = re.compile(kind)
        if pattern.match(ast_node.get_kind()):
            yield ast_node
        for child in ast_node.get_children():
            assert isinstance(child, type(ast_node)), f'Expected {type(ast_node)} but got {type(child)}'
            yield from ASTFinder.__matches_kind(child, kind) 


import re
from typing import Callable, Iterator, Optional

from common import Stream
from .ast_node import ASTNode, ASTNodeType

class ASTFinder:
    KIND_MATCH = re.compile(r'[\W_]+')
    @staticmethod
    def find_all(ast_node: ASTNodeType, function: Callable[[ASTNodeType], Iterator[ASTNodeType]|bool])-> Stream[ASTNodeType]:
        return Stream(ASTFinder.__find_all(ast_node, function))

    @staticmethod
    def find_kind(ast_node: ASTNodeType, kind: str)-> Stream[ASTNodeType]:
        return Stream(ASTFinder.__matches_kind(ast_node, kind))

    @staticmethod
    def matches_kind(ast_node: Optional[ASTNode], kind: str)-> bool:
        # compare kind with the ast_node kind only using word characters
        # get kind of the ast_node with only word characters
        if ast_node == None:
            return False
        ast_kind = ASTFinder.KIND_MATCH.sub('', ast_node.get_kind()).lower()
        pattern = kind if isinstance(kind, re.Pattern) else re.compile(kind, re.IGNORECASE)
        return pattern.fullmatch(ast_kind) != None

    @staticmethod
    def __find_all(ast_node: ASTNodeType, function: Callable[[ASTNodeType], Iterator[ASTNodeType]|bool])-> Iterator[ASTNodeType]:
        result = function(ast_node)
        if isinstance(result, bool) and result:
            yield ast_node
        elif isinstance(result, Iterator):
            yield from result
        for child in ast_node.get_children():
            yield from ASTFinder.__find_all(child, function)

    @staticmethod
    def __matches_kind(ast_node: ASTNodeType, kind:str|re.Pattern)-> Iterator[ASTNodeType]:
        pattern = kind if isinstance(kind, re.Pattern) else re.compile(kind, re.IGNORECASE)
        ast_kind = ASTFinder.KIND_MATCH.sub('', ast_node.get_kind()).lower()

        if pattern.fullmatch(ast_kind):
            yield ast_node
        for child in ast_node.get_children():
            assert isinstance(child, type(ast_node)), f'Expected {type(ast_node)} but got {type(child)}'
            yield from ASTFinder.__matches_kind(child, pattern) 


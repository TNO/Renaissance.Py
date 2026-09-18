"""AI: Helpers for finding AST nodes matching a predicate or semantic kind."""

import re
from collections.abc import Callable, Iterator, Sequence

from renaissance.utils.ast_utils import traverse

from .ast_node import ASTNode
from .node_protocol import NodeProtocol
from .semantic_kind import SemanticKind


class ASTFinder:
    """AI: Static helpers for finding AST nodes matching a predicate or semantic kind."""

    KIND_MATCH = re.compile(r"[\W_]+")

    @staticmethod
    def find_all(ast_node: ASTNode, function: Callable[[ASTNode], Iterator[ASTNode] | bool]) -> Sequence[ASTNode]:
        """AI: Return all descendant nodes of ast_node for which function returns a truthy value or child iterator."""
        return list(ASTFinder.__find_all(ast_node, function))

    # @staticmethod
    # def find_kind(ast_node: ASTNode, kind: str | re.Pattern[str]) -> Sequence[ASTNode]:
    #     return list(ASTFinder.__matches_kind(ast_node, kind))

    @staticmethod
    def find(ast_node: ASTNode, kind: str | re.Pattern[str]) -> Sequence[ASTNode]:
        """AI: Return all descendant nodes of ast_node whose kind matches the given kind pattern."""
        return list(ASTFinder.__matches_kind(ast_node, kind))

    @staticmethod
    def matches_kind(ast_node: ASTNode | None, kind: str | re.Pattern[str]) -> bool:
        """AI: Return whether ast_node's kind matches the given kind pattern."""
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
        node_kind = ast_node.kind or ""
        ast_kind = ASTFinder.KIND_MATCH.sub("", node_kind).lower()

        if pattern.fullmatch(ast_kind):
            yield ast_node
        for child in ast_node.children:
            # assert isinstance(child, type(ast_node)), f'Expected {type(ast_node)} but got {type(child)}'
            yield from ASTFinder.__matches_kind(child, pattern)


def find_nodes(ast_node: NodeProtocol, predicate) -> Sequence[NodeProtocol]:
    """AI: Return all descendants (and ast_node itself) matching predicate, via a full traversal."""
    return [node for node in traverse(ast_node) if predicate(node)]


def matches_node(ast_node: NodeProtocol, predicate) -> bool:
    """AI: Return True if ast_node itself satisfies predicate."""
    return predicate(ast_node)


def find_semantic_kind(ast_node: NodeProtocol, kind: SemanticKind) -> Sequence[NodeProtocol]:
    """AI: Return all nodes under ast_node whose semantic kind matches the given kind."""
    return find_nodes(ast_node, lambda node: node.semantic_kind is kind)

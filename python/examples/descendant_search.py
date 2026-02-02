from common import Stream
from syntax_tree.match_finder import PatternMatch, MatchFinder
from syntax_tree.ast_node import ASTNode


def find_descendant_match(
    root: ASTNode, outer_pattern: ASTNode, inner_pattern: ASTNode
) -> Stream[PatternMatch]:
    return MatchFinder.find_all(root, [outer_pattern]).flat_map(
        lambda match: MatchFinder.find_all(match.nodes, [inner_pattern])
    )

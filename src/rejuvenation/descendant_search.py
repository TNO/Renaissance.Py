"""AI: Example helper for matching nested (descendant) AST patterns."""

from arpeggio import flatten

from renaissance.syntax_tree import PatternMatch
from renaissance.syntax_tree.ast_node import ASTNode
from renaissance.syntax_tree.match_finder import match_pattern


def find_descendant_match(root: ASTNode, outer_pattern: ASTNode, inner_pattern: ASTNode) -> list[PatternMatch]:
    """AI: Return matches of `inner_pattern` nested within nodes matching `outer_pattern`."""
    return flatten(match_pattern(match.nodes, [inner_pattern]) for match in match_pattern(root.children, [outer_pattern]))

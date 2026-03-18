from renaissance.common import Stream
from renaissance.syntax_tree import PatternMatch, MatchFinder
from renaissance.syntax_tree.ast_node import ASTNode


class TestDescendantSearch:
    def find_descendant_match(self,
        root: ASTNode, outer_pattern: ASTNode, inner_pattern: ASTNode
    ) -> Stream[PatternMatch]:
        return MatchFinder.find_all(root.children, [outer_pattern]).flat_map(
            lambda match: MatchFinder.find_all(match.nodes, [inner_pattern])
        )




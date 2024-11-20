from typing import TypeVar
from syntax_tree.ast_finder import ASTFinder
from syntax_tree.ast_node import ASTNode
from syntax_tree.ast_refactor import ASTRefactor

ASTNodeType = TypeVar('ASTNodeType', bound=ASTNode)

class CleanupRefactoring:
    def __init__(self):
        raise Exception("This class should not be instantiated")

    @staticmethod
    def remove_unused_variables(ast_refactor: ASTRefactor[ASTNodeType]) -> ASTRefactor:
        """
        Removes all unused variables from a function
        """
        ast_refactor.find_kind('(?i)Compound_?Stmt').\
            flat_map(lambda func: ASTFinder.find_kind(func,'(?i)Var_?Decl')).\
            filter(lambda node: len(node.get_referenced_by())==0).\
            map(lambda node: node.get_parent()).\
            for_each(lambda node: ast_refactor.remove(node, True, True))
        return ast_refactor.commit()
        
        
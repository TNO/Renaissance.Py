from more_itertools import flatten

from renaissance.impl.types import VariableDeclaration, CompoundStatement
from renaissance.syntax_tree import ASTProcessor
from renaissance.syntax_tree.ast_finder import find_ast_type


class CleanupRefactoring:
    def __init__(self):
        raise Exception("This class should not be instantiated")

    @staticmethod
    def remove_unused_variables(ast_refactor: ASTProcessor) -> None:
        """
        Removes all unused variables from a function
        """
        refs = flatten(find_ast_type(n, VariableDeclaration) for n in find_ast_type(ast_refactor.node, CompoundStatement))
        [ast_refactor.remove(ref.parent, True, True) for ref in refs if len(ref.referenced_by) == 0]

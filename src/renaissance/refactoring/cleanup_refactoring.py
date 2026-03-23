from more_itertools import flatten

from renaissance.syntax_tree import ASTFinder, ASTProcessor


class CleanupRefactoring:
    def __init__(self):
        raise Exception("This class should not be instantiated")

    @staticmethod
    def remove_unused_variables(ast_refactor: ASTProcessor) -> None:
        """
        Removes all unused variables from a function
        """
        refs = flatten(ASTFinder.find_kind(n, "(?i)Var_?Decl") for n in ast_refactor.find_kind("(?i)Compound_?Stmt"))
        (ast_refactor.remove(ref.parent, True, True)
         for ref in refs if len(ref.referenced_by) == 0)

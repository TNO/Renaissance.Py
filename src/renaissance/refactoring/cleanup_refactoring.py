from renaissance.syntax_tree import ASTFinder, ASTProcessor

class CleanupRefactoring:
    def __init__(self):
        raise Exception("This class should not be instantiated")

    @staticmethod
    def remove_unused_variables(ast_refactor: ASTProcessor) -> None:
        """
        Removes all unused variables from a function
        """
        ast_refactor.find_kind('(?i)Compound_?Stmt').\
            flat_map(lambda func: ASTFinder.find_kind(func,'(?i)Var_?Decl')).\
            filter(lambda node: len(node.referenced_by) == 0).\
            map(lambda node: node.parent).\
            for_each(lambda node: ast_refactor.remove(node, True, True)) # type: ignore
        
        
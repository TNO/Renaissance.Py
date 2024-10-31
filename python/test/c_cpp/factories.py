from itertools import product
from impl.clang.clang_ast_node import ClangASTNode
from impl.clang_json.clang_json_ast_node import ClangJsonASTNode
from syntax_tree.ast_factory import ASTFactory

class Factories():
    # add factories here to test different ASTNode implementations
    factories = [ ('clang', ASTFactory(ClangASTNode)), ('clang_json', ASTFactory(ClangJsonASTNode)) ]
    
    @staticmethod
    def extend(test_parameters: list[tuple]) -> list[tuple]:
        """
        Combines a list of tuples with factory tuples to generate a new list of tuples.

        Args:
            test_parameters (list[tuple]): A list of tuples where each tuple contains test parameters to be combined with factory tuples.

        Returns:
            list[tuple]: A new list of tuples where each tuple is a combination of a name and factory tuple and a parameter tuple.
            the original parameter tuple is expanded with the factory name and the factory instance. So two new args must be added to test.
        """
        result=  [ (factory[0]+' '+ pars[0], factory[1], *pars) for factory, pars in product(Factories.factories, test_parameters)]
        return result

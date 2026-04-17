from itertools import product

from renaissance.impl.clang import ClangASTNode
from renaissance.impl.clang_json import ClangJsonASTNode
from renaissance.syntax_tree import ASTFactory


class Factories:
    # add factories here to test different ASTNode implementations
    node_types = [("clang", ClangASTNode), ("clang_json", ClangJsonASTNode)]
    factories = [(name_type[0], ASTFactory(name_type[1])) for name_type in node_types]

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
        result = [
            (str(factory[0]) + " " + str(pars[0]), factory[1], *pars) for factory, pars in product(Factories.factories, test_parameters)
        ]
        return result

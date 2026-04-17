from ast import AST
from itertools import product
from renaissance.impl.python.python_ast_node import PythonASTNode
from renaissance.impl.python.python_cst_node import PythonCstNode
from renaissance.impl.tree_sitter.lst import LSTNode
from renaissance.syntax_tree.ast_factory import ASTFactory


class Factories:
    # add factories here to test different ASTNode implementations
    node_types = [("ast", PythonASTNode),
                  ("cst", PythonCstNode),
                  ("lst", LSTNode),
                  ("rst", AST),]
    factories = [(name_type[0], ASTFactory(name_type[1])) for name_type in node_types]

    @staticmethod
    def extend(test_parameters: list[tuple]) -> list[tuple]:
        result = [
            (str(factory[0]) + " " + str(pars[0]), factory[1], *pars) for factory, pars in product(Factories.factories, test_parameters)
        ]
        return result

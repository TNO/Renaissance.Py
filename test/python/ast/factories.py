import ast
from itertools import product

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.integrations.python.ast.factory import PythonFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.integrations.tree_sitter.lst import LSTNode


class Factories:
    # add factories here to test different ASTNode implementations
    node_types = [
        ("ast", ast.AST),
        ("cst", PythonCstNode),
        ("lst", LSTNode),
        ("rst", PythonRstNode),
    ]
    factories = [(name_type[0], PythonFactory(name_type[1])) for name_type in node_types]

    @staticmethod
    def extend(test_parameters: list[tuple]) -> list[tuple]:
        result = [
            (str(factory[0]) + " " + str(pars[0]), factory[1], *pars) for factory, pars in product(Factories.factories, test_parameters)
        ]
        return result

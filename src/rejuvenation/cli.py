#! /usr/bin/python3
from renaissance.refactoring.pyunit_to_pytest_refactor import convert
from renaissance.syntax_tree import ASTFactory
from renaissance.impl import PythonASTNode
import sys


def refactor():
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create(sys.argv[1])
    return convert(atu)

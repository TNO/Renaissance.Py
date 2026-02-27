#! /usr/bin/python3
from renaissance.refactoring.taut2pyunit
from renaissance.syntax_tree import ASTFactory
from renaissance.impl.python import PythonASTNode
import sys

factory = ASTFactory(PythonASTNode, [])


def convert(taut):
    taut_atu = factory.create(taut)
    result = convert(taut_atu)
    if result.has_changes:
        with open(taut, 'w') as f:
            f.write(result.apply_to_string())


def refactor(taut):
    for taut in dir(sys.argv[1]):
        convert(taut)


def refactor():
    factory = ASTFactory(PythonASTNode, [])
    for taut in dir(sys.argv[1]):
        taut_atu = factory.create(taut)
        result = convert(taut_atu)
        if result:
            with open(taut, 'w') as f:
                f.write(result)

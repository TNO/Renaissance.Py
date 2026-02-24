#! /usr/bin/python3
from refactoring.pyunit_to_pytest_refactor import convert_test_cases, convert
from syntax_tree import ASTFactory, CPatternFactory, MatchFinder, ASTRewriter
from impl.python import PythonASTNode, PythonPatternFactory
import sys


def refactor():
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create(sys.argv[1])
    return convert(atu)

#! /usr/bin/python3
from pathlib import Path

from renaissance.refactoring.taut2pyunit import TautRefactoring
from renaissance.syntax_tree import ASTFactory, ASTRewriter
from renaissance.impl.python import PythonASTNode, PythonPatternFactory
import sys

from renaissance.syntax_tree.match_finder import match_pattern

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


# def refactor():
#     factory = ASTFactory(PythonASTNode, [])
#     for taut in dir(sys.argv[1]):
#         taut_atu = factory.create(taut)
#         result = convert(taut_atu)
#         if result:
#             with open(taut, 'w') as f:
#                 f.write(result)

def select_pyton_file():

    # is_python_file = lambda file_path: file_path.is_file() and file_path.suffix.lower() == '.py'
    current_dir = Path('.')
    print(f'refactor in {current_dir.resolve()}')

    return current_dir.glob('**/*.py')
    # return (file_path for file_path in current_dir.iterdir() if is_python_file)


def convert_pytest(file):
    print(file)
    test_atu = factory.create(file)
    pattern_factory = PythonPatternFactory(factory, None)
    unittest = pattern_factory.create_statements('import unittest')
    rewriter = ASTRewriter(test_atu)
    for match in match_pattern(test_atu.children, unittest):
        rewriter.replace('import pytest',match.nodes)
    if rewriter.has_changed():
        with open(file, 'w') as f:
            f.write(rewriter.apply_to_string())


if __name__ == "__main__":
    for file in select_pyton_file():
        # print(file.resolve())
        convert_pytest(file)
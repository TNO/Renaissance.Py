import ast
from selectors import SelectSelector

from common import Stream
from refactoring.pyunit_to_pytest_refactor import convert_test_cases
#This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
#It specifically showcases nested replacements and multiple patterns.
from syntax_tree import ASTFactory, CPatternFactory, MatchFinder, ASTRewriter
from impl.python import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTShower, TextUtils, ASTFinder


def refactor(test_file):
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create(test_file)
    return convert(atu)


if __name__ == "__main__":
    import sys

    test_file = sys.argv[1]
    result = refactor(test_file)
    with open(test_file, 'w') as f:
        f.write(result)
    print(result)


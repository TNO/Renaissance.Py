import ast
from selectors import SelectSelector

from common import Stream
from refactoring.pyunit_to_pytest_refactor import convert_test_cases
#This script demonstrates the use of the syntax_tree library to parse and rewrite C code.
#It specifically showcases nested replacements and multiple patterns.
from syntax_tree import ASTFactory, CPatternFactory, MatchFinder, ASTRewriter
from impl.python import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTShower, TextUtils, ASTFinder

#
# def refactor(match):
#     if match.patterns == pattern1:
#         replment_text = pattern1replacement
#     else:
#         replment_text = pattern2replacement
#
#     pattern1 = pattern_factory.create_statements('if pa(): $$stmts')
#     # for pattern 2 we create a fully functional c snippet with a call to f1
#     # note that the f1 declaration is derived from the atu
#     pattern2 = pattern_factory.create_expression('na($a)')
#     ASTShower.show_node(pattern1[0], include_properties=True)
#
#     # the replacement code strip indent is used to be agnostic to the indentation of the replacement
#     pattern1replacement = TextUtils.strip_indent("""
#             # changed if expr to const
#             isAOne=True
#             if(isAOne):
#                 $$stmts
#             """)
#     pattern2replacement = '# changed function f1 to f2\nf2($a,123456)\n'
#
#     # show node and patterns enable include properties to show the properties of the nodes
#     include_properties = True
#     ASTShower.show_node(atu, include_properties)
#     ASTShower.show_node(pattern1[0], include_properties)
#     ASTShower.show_node(pattern2, include_properties)
#
#     result = None
#
#
# def raw(nodes):
#     res = ''
#     for node in nodes:
#         res += node.text
#     return res + '\n'
#     factory = ASTFactory(PythonASTNode, args[1:])

def refactor(args):
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create(args[1])
    return convert_test_cases(atu)


if __name__ == "__main__":
    import sys

    result = refactor(sys.argv)
    with open(sys.argv[1], 'w') as f:
        f.write(result)
    print(result)


from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFinder, ASTProcessor, MatchFinder, ASTRewriter, ASTFactory
from renaissance.syntax_tree.match_finder import match_pattern

factory = ASTFactory(PythonASTNode, [])
pattern_factory = PythonPatternFactory(factory, None)
PYUNIT_TEST_CASE_PATTERN='def $test_case(self):\n    $$aaa'
PYTEST_REPLACEMENT = 'def $test_case():\n    $$aaa'

def raw(nodes):
    res = ''
    for node in nodes:
        res += '\n\n    ' + node.text
    return res + '\n    '

def convert_pytest(file):
    print(file)
    test_atu = factory.create(file)
    pattern_factory = PythonPatternFactory(factory, None)
    rewriter = ASTRewriter(test_atu)

    unittest = pattern_factory.create_statements('import unittest')
    for match in match_pattern(test_atu.children, unittest):
        rewriter.replace('import pytest',match.nodes,False, False)



    unittest = pattern_factory.create_statements('self.assertEqual($exp, $act)')
    for match in match_pattern(test_atu.children, unittest):
        act = match.expansions['$act']
        exp = match.expansions['$exp']
        rewriter.replace(f'assert_that({act}, is_({exp}))',match.nodes,False, False)

    test_main = pattern_factory.create_statements('class $klass(unittest.TestCase):\n    $$test_cases\n')
    for match in match_pattern(test_atu.children, test_main):
        repl = f'class {match.expansions["$klass"][0]}:\n{raw(match.expansions["$$test_cases"])}'
        rewriter.replace(repl, match.nodes, True, True)

    test_main = pattern_factory.create_statements('unittest.main()')
    for match in match_pattern(test_atu.children, test_main):
        rewriter.replace('pytest.main()',match.nodes, False, False)

    if rewriter.has_changed():
        with open(file, 'w') as f:
            f.write(rewriter.apply_to_string())

# def raw(nodes):
#     res = ''
#     for node in nodes:
#         if isinstance(node, PythonASTNode):
#             res += node.signature + '\n        '
#         else:
#             res += str(node)
#     return res #+ '\n'


def convert_test_cases(atu):
    pyunit_case = pattern_factory.create_statements(PYUNIT_TEST_CASE_PATTERN)
    test_cases = MatchFinder.find_all(atu.children, pyunit_case).to_iterable()
    rewriter = ASTRewriter(atu)
    for test_case in test_cases:
        pytest_replacement = PYTEST_REPLACEMENT
        for snippets in test_case.expansions:
            pytest_replacement = pytest_replacement.replace(snippets, raw(test_case.expansions[snippets]))
        rewriter.replace(pytest_replacement, test_case.nodes)
    return rewriter.apply_to_string()

def remove_class(atu):
    pyunit_class = pattern_factory.create_statements('class $TestExample(TestCase):\n    $$cases')
    test_class = MatchFinder.find_all(atu.children, pyunit_class).to_iterable()
    rewriter = ASTRewriter(atu)
    for klass in test_class:
        pytest_replacement = 'class $TestExample:\n  $$cases'
        for snippets in klass.expansions:
            pytest_replacement = pytest_replacement.replace('$$cases', raw(klass.expansions[snippets]))
        rewriter.replace(pytest_replacement, klass.nodes)
    return rewriter.apply_to_string()
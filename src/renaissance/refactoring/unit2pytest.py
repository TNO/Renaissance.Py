from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTFinder, ASTProcessor, MatchFinder, ASTRewriter, ASTFactory, ASTNode
from renaissance.syntax_tree.match_finder import match_pattern

factory = ASTFactory(PythonASTNode, [])
pattern_factory = PythonPatternFactory(factory, None)
PYUNIT_TEST_CASE_PATTERN = 'def $test_case(self):\n    $$aaa'
PYTEST_REPLACEMENT = 'def $test_case():\n    $$aaa'


def raw(nodes):
    res = ''
    for node in nodes:
        res += '\n\n    ' + node.text
    return res + '\n    '


def convert_pytest(file):
    print(file)
    pattern_factory = PythonPatternFactory(factory, None)

    test_atu2 = factory.create(file)
    rewriter2 = ASTRewriter(test_atu2)
    convert_test_class(pattern_factory, rewriter2, test_atu2)
    if rewriter2.has_changed():
        with open(file, 'w') as f:
            f.write(rewriter2.apply_to_string())

    test_atu = factory.create(file)

    rewriter = ASTRewriter(test_atu)

    convert_test_import(pattern_factory, rewriter, test_atu)
    convert_assert_equals(pattern_factory, rewriter, test_atu)
    convert_assert_greater(pattern_factory, rewriter, test_atu)
    convert_assert_true(pattern_factory, rewriter, test_atu)

    convert_plain_assert_not_empty(pattern_factory, rewriter, test_atu)
    convert_plain_assert_same_length(pattern_factory, rewriter, test_atu)
    convert_plain_assert_string(pattern_factory, rewriter, test_atu)
    convert_plain_assert_equal(pattern_factory, rewriter, test_atu)

    remove_print(pattern_factory, rewriter, test_atu)

    convert_test_setup(pattern_factory, rewriter, test_atu)
    convert_test_main(pattern_factory, rewriter, test_atu)
    if rewriter.has_changed():
        with open(file, 'w') as f:
            f.write(rewriter.apply_to_string())
    # post proc
    hamcrest_atu = factory.create(file)

    rewriter3 = ASTRewriter(hamcrest_atu)

    convert_assert_that_equal_len(pattern_factory, rewriter3, hamcrest_atu)

    if rewriter3.has_changed():
        with open(file, 'w') as f:
            f.write(rewriter3.apply_to_string())

def convert_test_import(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    unittest = pattern_factory.create_statements('import unittest')
    for match in match_pattern(test_atu.children, unittest):
        rewriter.replace('import pytest\nfrom hamcrest import *', match.nodes, False, False)


def convert_test_class(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    test_main = pattern_factory.create_statements('class $klass(unittest.TestCase):\n    $$test_cases\n')
    for match in match_pattern(test_atu.children, test_main):
        repl = match.nodes[0].signature.replace('(unittest.TestCase):', ':')
        # repl = f'class {match.expansions["$klass"][0]}:\n{raw(match.expansions["$$test_cases"])}'
        rewriter.replace(repl, match.nodes, False, False)

    test_main = pattern_factory.create_statements('class $klass(TestCase):\n    $$test_cases\n')
    for match in match_pattern(test_atu.children, test_main):
        repl = match.nodes[0].signature.replace('(TestCase):', ':')
        # repl = f'class {match.expansions["$klass"][0]}:\n{raw(match.expansions["$$test_cases"])}'
        rewriter.replace(repl, match.nodes, False, False)


def convert_test_setup(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    test_main = pattern_factory.create_statements('def setUp(self): $$stmts')
    for match in match_pattern(test_atu.children, test_main):
        stmts = raw(match.expansions['$$stmts'])
        repl = f'@pytest.fixture(autouse=True)\n{match.nodes[0].signature}'
        rewriter.replace(repl, match.nodes, False, False)


def convert_test_main(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    test_main = pattern_factory.create_statements('unittest.main()')
    for match in match_pattern(test_atu.children, test_main):
        rewriter.replace('pytest.main()', match.nodes, False, False)


def convert_assert_equals(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    unittest = pattern_factory.create_statements('self.assertEqual($exp, $act)')
    for match in match_pattern(test_atu.children, unittest):
        act = match.expansions['$act'][0].signature
        exp = match.expansions['$exp'][0].signature
        if match.expansions['$act'][0].kind in ['Constant']:
            repl = f'assert_that({exp}, is_({act}))'
        else:  # original is wrong
            repl = f'assert_that({act}, is_({exp}))'
        rewriter.replace(repl, match.nodes, False, False)

def convert_assert_that_equal_len(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    pattern = pattern_factory.create_statements('assert_that(len($act), is_($exp))')
    for match in match_pattern(test_atu.children, pattern):
        act = match.expansions['$act'][0].signature
        exp = match.expansions['$exp'][0].signature
        repl = f'assert_that({act}, has_length({exp}))'
        rewriter.replace(repl, match.nodes, False, False)


def convert_assert_greater(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    unittest = pattern_factory.create_statements('self.assertGreater($exp, $act)')
    for match in match_pattern(test_atu.children, unittest):
        act = match.expansions['$act'][0].signature
        exp = match.expansions['$exp'][0].signature
        if match.expansions['$act'][0].kind in ['Constant']:
            repl = f'assert_that({exp}, greater_than({act}))'
        else:  # original is wrong
            repl = f'assert_that({act}, greater_than({exp}))'
        rewriter.replace(repl, match.nodes, False, False)


def convert_assert_true(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    unittest = pattern_factory.create_statements('self.assertTrue($act)')
    for match in match_pattern(test_atu.children, unittest):
        act = match.expansions['$act'][0].signature
        repl = f'assert_that({act})'
        rewriter.replace(repl, match.nodes, False, False)


def convert_plain_assert_not_empty(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    unittest = pattern_factory.create_statements('assert  len($exp) >= 1')
    for match in match_pattern(test_atu.children, unittest):
        exp = match.expansions['$exp'][0].signature
        repl = f'assert_that({exp}, is_not(empty()))'
        rewriter.replace(repl, match.nodes, False, False)


def convert_plain_assert_same_length(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    unittest = pattern_factory.create_statements('assert  len($exp) == $length')
    for match in match_pattern(test_atu.children, unittest):
        exp = match.expansions['$exp'][0].signature
        length = match.expansions['$length'][0].signature
        repl = f'assert_that({exp}, has_length({length}))'
        rewriter.replace(repl, match.nodes, False, False)


def convert_plain_assert_string(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    unittest = pattern_factory.create_statements('assert str($act) == $exp')
    for match in match_pattern(test_atu.children, unittest):
        exp = match.expansions['$exp'][0].signature
        act = match.expansions['$act'][0].signature
        repl = f'assert_that({act}, has_string({exp}))'
        rewriter.replace(repl, match.nodes, False, False)


def convert_plain_assert_equal(pattern_factory, rewriter, test_atu):
    unittest = pattern_factory.create_statements('assert $exp == $act')
    for match in match_pattern(test_atu.children, unittest):
        exp = match.expansions['$exp'][0].signature
        act = match.expansions['$act'][0].signature
        repl = f'assert_that({act}, is_({exp}))'
        rewriter.replace(repl, match.nodes, False, False)


def remove_print(pattern_factory: PythonPatternFactory, rewriter: ASTRewriter, test_atu: ASTNode):
    print_msg = pattern_factory.create_statements('print($$msg)')
    for match in match_pattern(test_atu.children, print_msg):
        rewriter.remove(match.nodes, False, False)


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

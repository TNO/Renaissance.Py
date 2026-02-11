from impl.python import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTFinder, ASTProcessor, MatchFinder, ASTRewriter, ASTFactory

factory = ASTFactory(PythonASTNode, [])
PYUNIT_TEST_CASE_PATTERN='def $test_case(self):\n    $$aaa'
PYTEST_REPLACEMENT = 'def $test_case():\n    $$aaa'


def raw(nodes):
    res = ''
    for node in nodes:
        if isinstance(node, PythonASTNode):
            res += node.signature + '\n        '
        else:
            res += str(node)
    return res #+ '\n'
def convert_test_cases(pattern_factory,atu, rewriter):
    pyunit_case = pattern_factory.create_statements(PYUNIT_TEST_CASE_PATTERN)
    test_cases = MatchFinder.find_all(rewriter.atu, pyunit_case).to_iterable()
    for test_case in test_cases:
        pytest_replacement = PYTEST_REPLACEMENT
        for snippets in test_case.expansions:
            pytest_replacement = pytest_replacement.replace(snippets, raw(test_case.expansions[snippets]))
        rewriter.replace(pytest_replacement, test_case.nodes)
    rewriter.apply()

def remove_class(pattern_factory,atu, rewriter):
    pyunit_class = pattern_factory.create_statements('class $TestExample(TestCase):\n    $$cases')
    test_class = MatchFinder.find_all(atu, pyunit_class).to_iterable()
    for klass in test_class:
        pytest_replacement = 'class $TestExample:\n  $$cases'
        for snippets in klass.expansions:
            pytest_replacement = pytest_replacement.replace('$$cases', raw(klass.expansions[snippets]))
        rewriter.replace(pytest_replacement, klass.nodes)

def convert(atu):
    rewriter = ASTRewriter(atu)
    pattern_factory = PythonPatternFactory(factory, atu)
    remove_class(pattern_factory, atu, rewriter)
    # convert_test_cases(pattern_factory, atu, rewriter)
    rewriter.apply()
    return rewriter.apply_to_string()
from impl.python import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTFinder, ASTProcessor, MatchFinder, ASTRewriter, ASTFactory, ASTNode

factory = ASTFactory(PythonASTNode, [])
TAUT_TEST_CASE_PATTERN='import TAUT'
PYUNIT_REPLACEMENT = ''

class TautRefactoring:
    def __init__(self, atu):
        raise  Exception('This class should not be instantiated')

    def raw(self, nodes):
        res = ''
        for node in nodes:
            if isinstance(node, PythonASTNode):
                res += node.signature + '\n        '
            else:
                res += str(node)
        return res #+ '\n'

    @staticmethod
    def remove_import(ast_refactor: ASTProcessor) -> None:
        """
        Remove import TAUT
        """
        ast_refactor.find_kind()

    @staticmethod
    def convert_test_cases(input_code):
        atu = factory.create_from_text(input_code, "test_import.py")
        rewriter = ASTRewriter(atu)
        ast_refactor = ASTProcessor(atu, factory, in_memory=True)
        pattern_factory = PythonPatternFactory(factory, atu)
        taut_case = pattern_factory.create_statements(TAUT_TEST_CASE_PATTERN)

        test_cases = MatchFinder.find_all(atu, taut_case).to_iterable()
        for test_case in test_cases:
            pytest_replacement = PYUNIT_REPLACEMENT
            for node in test_case.nodes:
                if node.kind == 'Import':
                    rewriter.remove(test_case)
        return ast_refactor.commit().apply_to_string()
import ast

from impl.python import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTShower, ASTProcessor, MatchFinder, ASTRewriter, ASTFactory

factory = ASTFactory(PythonASTNode, [])
TAUT_TEST_CASE_PATTERN='import TAUT'
PYUNIT_REPLACEMENT = ''

class TautRefactoring:
    def __init__(self, atu):
        raise  Exception('This class should not be instantiated')

    @classmethod
    def raw(self, nodes, multi_nodes: bool = False) -> str:
        res = ''
        start_offset = 0
        end_offset = 0
        if multi_nodes:
            for node in nodes:
                if isinstance(node, PythonASTNode):
                    if start_offset == 0 or node.offset < start_offset:
                        start_offset = node.offset
                    if end_offset == 0 or node.end_offset > end_offset :
                        end_offset = node.end_offset
            return node.root.content(start_offset, end_offset)
        for node in nodes:
            if isinstance(node, PythonASTNode):
                match node.kind:
                    case 'Pass':
                        res += 'pass'
                    case _:
                        res += node.signature
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
        pattern_factory = PythonPatternFactory(factory, atu)
        taut_case = pattern_factory.create_statements(TAUT_TEST_CASE_PATTERN)

        test_cases = MatchFinder.find_all(atu, taut_case).to_iterable()
        for test_case in test_cases:
            rewriter.remove(test_case.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @staticmethod
    def remove_import_taut(ast_refactor: ASTProcessor) -> None:
        """
        Removes import TAUT
        """
        ast_refactor.find_kind('Import').\
            filter(lambda node: node.name.find('TAUT') > 0).\
            for_each(lambda node: ast_refactor.remove(node, True, True))

    @staticmethod
    def replace_taut(input_code):
        """
        replace TAUT.TestCase by unittest.TestCase
        """
        atu = factory.create_from_text(input_code, "test_class.py")
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        pattern = 'class $test_case(TAUT.TestCase):\n    $$aaa'
        pyunit_replacement = 'class $test_case(unittest.TestCase):\n    $$aaa'
        class_def = pattern_factory.create_python_pattern(pattern)

        test_cases = MatchFinder.find_all(atu, class_def).to_iterable()
        for test_case in test_cases:
            replacement = pyunit_replacement
            for snippets in test_case.expansions:
                replacement = replacement.replace(snippets, TautRefactoring.raw(test_case.expansions[snippets]))
            rewriter.replace(replacement, test_case.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @staticmethod
    def replace_taut_skip(ast_refactor):
        """
        replace @TAUT.skip_test by @unittest.skip
        """
        ast_refactor.find_kind('Attribute'). \
            filter(lambda node: node.name == 'TAUT.skip_test'). \
            for_each(lambda node: ast_refactor.replace('unittest.skip', node))

    @staticmethod
    def replace_mock_import(input_code):
        """
        replace mock by unittest.mock and using patch
        """
        atu = factory.create_from_text(input_code, 'import_2.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        pattern1 = 'import mock\n'
        pattern2 = 'from TAUT import TestCase, TestDoubles'
        pyunit_replacement = 'try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n'
        import_pattern1 = pattern_factory.create_python_pattern(pattern1)
        import_pattern2 = pattern_factory.create_python_pattern(pattern2)

        match1 = MatchFinder.find_all(atu, import_pattern1).to_iterable()
        for test_case in match1:
            rewriter.remove(test_case.nodes)
        match2 = MatchFinder.find_all(atu, import_pattern2).to_iterable()
        rewriter.replace(pyunit_replacement, match2[0].nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @staticmethod
    def add_self(ast_refactor):
        """
        replace mock by unittest.mock and using patch
        """
        matching = ['emrwxread', 'emrwxwidxread', 'emrwxviprxinterface', 'whxstream2']
        ast_refactor.find_kind('Name'). \
            filter(lambda node: node.name in matching). \
            for_each(lambda node: ast_refactor.replace('self.' + node.name, node))
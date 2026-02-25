import ast
import os
import subprocess
import sys
import tempfile

from black import format_str, FileMode
from utils.flake8_util import fix_indent

from impl.python import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTShower, ASTProcessor, MatchFinder, ASTRewriter, ASTFactory

factory = ASTFactory(PythonASTNode, [])
PYUNIT_REPLACEMENT = ''

class TautRefactoring:
    def __init__(self, atu):
        raise  Exception('This class should not be instantiated')

    @staticmethod
    def remove_import_taut(ast_refactor: ASTProcessor) -> None:
        """
        Removes import TAUT
        """
        ast_refactor.find_kind('Import'). \
            filter(lambda node: node.name.find('TAUT') > 0). \
            for_each(lambda node: ast_refactor.remove(node, True, True))

    @staticmethod
    def replace_taut_skip(ast_refactor):
        """
        replace @TAUT.skip_test by @unittest.skip
        """
        ast_refactor.find_kind('Attribute'). \
            filter(lambda node: node.name == 'TAUT.skip_test'). \
            for_each(lambda node: ast_refactor.replace('@unittest.skip', node))

    @staticmethod
    def add_self(ast_refactor):
        """
        replace mock by unittest.mock and using patch
        """
        matching = ['emrwxread', 'emrwxwidxread', 'emrwxviprxinterface', 'whxstream2']
        ast_refactor.find_kind('Name'). \
            filter(lambda node: node.name in matching). \
            for_each(lambda node: ast_refactor.replace('self.' + node.name, node))

    @staticmethod
    def remove_decorator(ast_refactor):
        ast_refactor.find_kind('Attribute'). \
            filter(lambda node: node.name == 'TAUT.log_stub'). \
            for_each(lambda node: ast_refactor.remove(node))

    @staticmethod
    def convert_test_cases(input_code):
        return TautRefactoring.refactor_remove(input_code,'import TAUT')

    @staticmethod
    def replace_taut(input_code):
        """
        replace TAUT.TestCase by unittest.TestCase
        """
        match_pattern = 'class $test_case(TAUT.TestCase):\n    $$aaa'
        replacement = 'class $test_case(unittest.TestCase):\n    $$aaa'
        return TautRefactoring.refactor_replace(input_code, match_pattern, replacement)

    @staticmethod
    def replace_mock_import(input_code):
        """
        replace mock by unittest.mock and using patch
        """
        pattern1 = 'import mock\n'
        result = TautRefactoring.refactor_remove(input_code, pattern1)
        pattern2 = 'from TAUT import TestCase, TestDoubles'
        replacement = 'try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n'
        return TautRefactoring.refactor_replace(result, pattern2, replacement)

    @staticmethod
    def replace_log_emrwxtl(input_code):
        pattern1 = 'with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)):\n    log = TAUT.Logger()\n    $$aa'
        replace_pattern = 'fake_emrwxtl = FakeEMRWxTL(None)\n$$aa'
        result = TautRefactoring.refactor_replace(input_code, pattern1, replace_pattern)
        formatted_code = fix_indent(result)

        pattern2 = 'emrwxtl.$a($$bb)'
        result2 = TautRefactoring.refactor_replace(formatted_code, pattern2, 'fake_emrwxtl.$a($$bb)')

        pattern3 = '$c = emrwxtl.$a($$bb)'
        return TautRefactoring.refactor_replace(result2, pattern3, '$c = fake_emrwxtl.$a($$bb)')

    @staticmethod
    def insert_class(input_code, insert_code):
        insert_pattern = 'def b():\n    $$bb'
        return TautRefactoring.refactor_insert(input_code, insert_code, insert_pattern)

    @classmethod
    def refactor_replace(self, input_code: str, before: str, after: str):
        atu = factory.create_from_text(input_code, 'temp.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        before_pattern = pattern_factory.create_python_pattern(before)

        test_cases = MatchFinder.find_all([atu], [before_pattern]).to_iterable()
        for test_case in test_cases:
            replacement = after
            for snippets in test_case.expansions:
                replacement = replacement.replace(snippets, TautRefactoring.raw(test_case.expansions[snippets], snippets))
            rewriter.replace(replacement, test_case.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @classmethod
    def refactor_remove(self, input_code: str, match_str: str):
        atu = factory.create_from_text(input_code, 'temp.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        match_pattern = pattern_factory.create_python_pattern(match_str)

        matched = MatchFinder.find_all([atu], [match_pattern]).to_iterable()
        for ma in matched:
            rewriter.remove(ma.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @classmethod
    def refactor_insert(self, input_code: str, insert_code: str, match_str: str):
        atu = factory.create_from_text(input_code, 'temp.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        match_pattern = pattern_factory.create_python_pattern(match_str)

        matched = MatchFinder.find_all([atu], [match_pattern]).to_iterable()[0]
        rewriter.insert_after(insert_code, matched.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @classmethod
    def raw(self, nodes, snippets) -> str:
        res = ''
        start_offset = 0
        end_offset = 0
        if '$$' in snippets:
            for node in nodes:
                if isinstance(node, PythonASTNode):
                    if start_offset == 0 or node.offset < start_offset:
                        start_offset = node.offset
                    if end_offset == 0 or node.end_offset > end_offset:
                        end_offset = node.end_offset
            return node.root.content(start_offset, end_offset)
        else:
            for node in nodes:
                if isinstance(node, PythonASTNode):
                    match node.kind:
                        case 'Pass':
                            res += 'pass'
                        case _:
                            res += node.signature
                else:
                    res += str(node)
        return res  # + '\n'

import unittest
from parameterized import parameterized
from refactoring import TautRefactoring
from python.factories import Factories
from syntax_tree import ASTFactory, ASTShower, ASTProcessor

class TestTaut2Unittest(unittest.TestCase):

    @parameterized.expand(Factories.extend([
        ("import unittest\nimport TAUT\nimport DDXA", "import unittest\nimport DDXA"),
    ]))
    def test_remove_import_taut(self, _, factory: ASTFactory, input_code, expected_code):
        atu = factory.create_from_text(input_code, 'import.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, factory, in_memory=True)
        TautRefactoring.remove_import_taut(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        self.assertEqual(expected_code, result)

    @parameterized.expand(Factories.extend([
        ("import unittest\nimport TAUT\nimport DDXA", "import unittest\nimport DDXA"),
    ]))
    def test_remove_import(self, _, factory: ASTFactory, input_code, expected_code):
        result = TautRefactoring.convert_test_cases(input_code)
        self.assertEqual(expected_code, result)

    @parameterized.expand(Factories.extend([
        ("class ATestCase(TAUT.TestCase):\n    pass\n", "class ATestCase(unittest.TestCase):\n    pass\n"),
    ]))
    def test_replace_taut(self, _, factory: ASTFactory, input_code, expected_code):
        result = TautRefactoring.replace_taut(input_code)
        self.assertEqual(expected_code, result)

    @parameterized.expand(Factories.extend([
        ("@TAUT.skip_test\ndef test(a, b):\n    pass\n", "@unittest.skip\ndef test(a, b):\n    pass\n")
    ]))
    def test_replace_skip(self, _, factory: ASTFactory, input_code, expected_code):
        atu = factory.create_from_text(input_code, 'tautskip.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, factory, in_memory=True)
        TautRefactoring.replace_taut_skip(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        self.assertEqual(expected_code, result)

    @parameterized.expand(Factories.extend([
        ("import mock\nfrom TAUT import TestCase, TestDoubles", "\ntry:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n")
    ]))
    def test_replace_import(self, _, factory: ASTFactory, input_code, expected_code):
        result = TautRefactoring.replace_mock_import(input_code)
        self.assertEqual(expected_code, result)

    @parameterized.expand(Factories.extend([
        ('emrwxread = 0', 'self.emrwxread = 0'),
        ('func(emrwxwidxread)', 'func(self.emrwxwidxread)'),
        ('a = test(emrwxviprxinterface)', 'a = test(self.emrwxviprxinterface)'),
        ('b = whxstream2', 'b = self.whxstream2'),
    ]))
    def test_add_self(self, _, factory: ASTFactory, input_code, expected_code):
        atu = factory.create_from_text(input_code, 'add_self.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, factory, in_memory=True)
        TautRefactoring.add_self(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        self.assertEqual(expected_code, result)

    @parameterized.expand(Factories.extend([
        ('@TAUT.log_stub\ndef create_test_log(self, test_log_id):\n    pass\n', 'def create_test_log(self, test_log_id):\n    pass\n'),
    ]))
    def test_remove_decorator(self, _, factory: ASTFactory, input_code, expected_code):
        atu = factory.create_from_text(input_code, 'add_self.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, factory, in_memory=True)
        TautRefactoring.remove_decorator(ast_refactor)
        #self.assertEqual(expected_code, result)
        result = ast_refactor.commit().apply_to_string()
        self.assertEqual(expected_code, result)

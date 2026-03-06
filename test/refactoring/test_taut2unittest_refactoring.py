import pytest

from parameterized import parameterized
from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.refactoring import TautRefactoring
from test_data.test_code import taut_code, result_code
from test_data.test_insert import input_code, insert_code
from test_data.test_class import set_up, new_set_up, tear_down, new_tear_down
from test_data.test_testdoubles import test_doubles_fun, test_doubles_fun_new, test_doubles_class, test_doubles_class_new
from renaissance.syntax_tree import ASTFactory, ASTShower, ASTProcessor

class TestTaut2Unittest:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = ASTFactory(PythonASTNode, [])

    @pytest.mark.parametrize("input_code, expected_code", [
        ("import unittest\nimport TAUT\nimport DDXA", "import unittest\nimport DDXA"),
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_remove_import_taut(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, 'import.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        TautRefactoring.remove_import_taut(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        ("import unittest\nimport TAUT\nimport DDXA", "import unittest\nimport DDXA"),
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_remove_import(self, input_code, expected_code):
        result = TautRefactoring.convert_test_cases(input_code)
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        ("class ATestCase(TAUT.TestCase):\n    pass\n", "class ATestCase(unittest.TestCase):\n    pass\n"),
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_replace_taut(self, input_code, expected_code):
        result = TautRefactoring.replace_taut(input_code)
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        ("@TAUT.skip_test\ndef test(a, b):\n    pass\n", "@unittest.skip\ndef test(a, b):\n    pass\n")
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_replace_skip(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, 'tautskip.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        TautRefactoring.replace_taut_skip(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        ("import mock\nfrom TAUT import TestCase, TestDoubles", "\ntry:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n")
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_replace_import(self, input_code, expected_code):
        result = TautRefactoring.replace_mock_import(input_code)
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        ('emrwxread = 0', 'self.emrwxread = 0'),
        ('func(emrwxwidxread)', 'func(self.emrwxwidxread)'),
        ('a = test(emrwxviprxinterface)', 'a = test(self.emrwxviprxinterface)'),
        ('b = whxstream2', 'b = self.whxstream2'),
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_add_self(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, 'add_self.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        TautRefactoring.add_self(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        ('@TAUT.log_stub\ndef create_test_log(self, test_log_id):\n    pass\n', '\ndef create_test_log(self, test_log_id):\n    pass\n'),
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_remove_decorator(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, 'add_self.py')
        ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        TautRefactoring.remove_decorator(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        (taut_code, result_code)
    ])
    def test_log_emrwxtl(self, input_code, expected_code):
        result = TautRefactoring.replace_log_emrwxtl(input_code)
        assert expected_code == result

    @pytest.mark.parametrize("input_code, insert_code", [
        (input_code, insert_code)
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_insert_class(self, input_code, insert_code):
        result = TautRefactoring.insert_class(input_code, insert_code)
        assert input_code + insert_code +'\n' == result

    @pytest.mark.parametrize("input_code, expected_code", [
        (set_up, new_set_up)
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_setUp(self, input_code, expected_code):
        result = TautRefactoring.refactor_setup(input_code)
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        (tear_down, new_tear_down)
    ])
    def test_tearDown(self, input_code, expected_code):
        result = TautRefactoring.refactor_teardown(input_code)
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        (test_doubles_fun, test_doubles_fun_new)
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_testdoubles_fun(self, input_code, expected_code):
        result = TautRefactoring.refactor_testdoubles_fun(input_code)
        assert expected_code == result

    @pytest.mark.parametrize("input_code, expected_code", [
        (test_doubles_class, test_doubles_class_new)
    ])
    @pytest.mark.skip("Skipping all tests in this class")
    def test_testdoubles_class(self, input_code, expected_code):
        result = TautRefactoring.refactor_testdoubles_class(input_code)
        assert expected_code == result
import pytest

import renaissance.refactoring.taut2pyunit as taut_refactor
import test_data.test_class as tst_class
import test_data.test_code as tst_code
import test_data.test_insert as tst_insert
from renaissance.impl.python import PythonASTNode
from renaissance.syntax_tree import ASTFactory, ASTProcessor
from test_data.test_testdoubles import (test_doubles_fun, test_doubles_fun_new, test_doubles_class, \
                                        test_doubles_class_new)

class TestTaut2Unittest:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = ASTFactory(PythonASTNode, [])

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "import unittest\nimport TAUT\nimport DDXA",
                "import unittest\nimport DDXA",
            ),
        ],
    )
    def test_remove_import_taut(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, "import.py")
        # ASTShower.show_node(atu)
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        taut_refactor.remove_import_taut(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert result == expected_code

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "import unittest\nimport TAUT\nimport DDXA",
                "import unittest\nimport DDXA",
            ),
        ],
    )
    def test_remove_import(self, input_code, expected_code):
        result = taut_refactor.replace_taut_import(input_code)
        assert result == expected_code

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "class ATestCase(TAUT.TestCase):\n    pass\n",
                "class ATestCase(unittest.TestCase):\n    pass\n",
            ),
            (
                "class testUtils(TestCase, Asserter):\n    pass\n",
                "class testUtils(unittest.TestCase, Asserter):\n    pass\n",
            ),
        ],
    )
    def test_replace_taut(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, "taut_test.py")
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        taut_refactor.replace_taut(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert result == expected_code

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "@TAUT.skip_test\ndef test(a, b):\n    pass\n",
                "@unittest.skip\ndef test(a, b):\n    pass\n",
            )
        ],
    )
    def test_replace_skip(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, "tautskip.py")
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        taut_refactor.replace_taut_skip(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert result == expected_code

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "import mock\nfrom TAUT import TestCase, TestDoubles",
                "\ntry:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n",
            )
        ],
    )
    def test_replace_import(self, input_code, expected_code):
        result = taut_refactor.replace_mock_import(input_code)
        assert result == expected_code

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            ("emrwxread = 0", "self.emrwxread = 0"),
            ("func(emrwxwidxread)", "func(self.emrwxwidxread)"),
            ("a = test(emrwxviprxinterface)", "a = test(self.emrwxviprxinterface)"),
            ("b = whxstream2", "b = self.whxstream2"),
            (
                "self.assertEqual(emrwxread.method_called(0))",
                "self.assertEqual(self.emrwxread.method_called(0))",
            ),
            #('EMRWxREAD.emrwxread.set_retval(0)', 'self.emrwxread.set_retval(0)')
        ],
    )
    def test_add_self(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, "add_self.py")
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        taut_refactor.add_self(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert result == expected_code

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "@TAUT.log_stub\ndef create_test_log(self, test_log_id):\n    pass\n",
                "\ndef create_test_log(self, test_log_id):\n    pass\n",
            ),
        ],
    )
    def test_remove_decorator(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, "add_self.py")
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        taut_refactor.remove_decorator(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert result == expected_code

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            ("self.assert_equal(len(listA), 5)", "self.assertEqual(len(listA), 5)"),
        ],
    )
    def test_convert_assert(self, input_code, expected_code):
        atu = self.factory.create_from_text(input_code, "assert.py")
        ast_refactor = ASTProcessor(atu, self.factory, in_memory=True)
        taut_refactor.convert_assert(ast_refactor)
        result = ast_refactor.commit().apply_to_string()
        assert result == expected_code

    @pytest.mark.parametrize("input_code, expected_code", [(tst_code.taut_code, tst_code.result_code)])
    def test_log_emrwxtl(self, input_code, expected_code):
        result = taut_refactor.replace_log_emrwxtl(input_code)
        assert result == expected_code

    @pytest.mark.parametrize("input_code, insert_code", [(tst_insert.input_code, tst_insert.insert_code)])
    def test_insert_class(self, input_code, insert_code):
        result = taut_refactor.insert_class(input_code, insert_code)
        assert result == input_code + insert_code + "\n"

    @pytest.mark.parametrize("input_code, expected_code", [(tst_class.set_up, tst_class.new_set_up)])
    def test_setup(self, input_code, expected_code):
        result = taut_refactor.refactor_setup(input_code)
        assert result == expected_code

    @pytest.mark.parametrize("input_code, expected_code", [(tst_class.tear_down, tst_class.new_tear_down)])
    def test_teardown(self, input_code, expected_code):
        result = taut_refactor.refactor_teardown(input_code)
        assert result == expected_code

    @pytest.mark.parametrize("input_code, expected_code", [(test_doubles_fun, test_doubles_fun_new)])
    def test_testdoubles_fun(self, input_code, expected_code):
        result = taut_refactor.refactor_testdoubles_fun(input_code)
        assert result == expected_code

    @pytest.mark.parametrize("input_code, expected_code", [(test_doubles_class, test_doubles_class_new)])
    def test_testdoubles_class(self, input_code, expected_code):
        result = taut_refactor.refactor_testdoubles_class(input_code)
        assert result == expected_code

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [(tst_class.change_comment, tst_class.new_change_comment)],
    )
    def test_change_comment(self, input_code, expected_code):
        result = taut_refactor.insert_doc(input_code, "01-22-2026")
        # assert result == expected_code

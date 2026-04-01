import textwrap
from pathlib import Path

import pytest
from hamcrest import ends_with, assert_that, is_

import renaissance.refactoring.taut2_pyunit as taut_refactor

import targets
from renaissance.refactoring.taut2_pyunit import Taut2Pyunit
import test_data.test_class as tst_class
import test_data.test_code as tst_code
import test_data.test_insert as tst_insert
from renaissance.impl.python import PythonASTNode
from renaissance.syntax_tree import ASTFactory, ASTProcessor
import test_data.test_testdoubles as tst_testdoubles


class TestTaut2Unittest:

    def test_init(self):
        subject = Taut2Pyunit(Path(targets.__file__).parent / "taut/taut_test.py")
        assert_that(subject.filename, ends_with("taut_test.py"))

    def _create(self, mocker, text) -> Taut2Pyunit:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.syntax_tree.ast_factory.ASTFactory.create",
            return_value=PythonASTNode.load_from_text(code),
        )
        subject = Taut2Pyunit("x.py")
        return subject

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "import unittest\nimport TAUT\nimport DDXA",
                "import unittest\nimport DDXA",
            ),
        ],
    )
    def test_remove_import(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.remove_taut_import()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

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
    def test_replace_taut(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.replace_taut()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "@TAUT.skip_test\ndef test(a, b):\n    pass\n",
                "@unittest.skip\ndef test(a, b):\n    pass\n",
            )
        ],
    )
    def test_replace_skip(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.replace_taut_skip()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize("input_code, expected_code",
    [
        (tst_testdoubles.test_indent, tst_testdoubles.test_indent_new),
        (tst_testdoubles.test_indent_fun, tst_testdoubles.test_indent_fun_new)
    ])
    def test_indentation(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.move_indent()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "import mock\nfrom TAUT import TestCase, TestDoubles",
                "\ntry:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n",
            )
        ],
    )
    def test_replace_import(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.replace_taut_import()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

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
            # ('EMRWxREAD.emrwxread.set_retval(0)', 'self.emrwxread.set_retval(0)')
        ],
    )
    def test_add_self(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.add_self()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            (
                "@TAUT.log_stub\ndef create_test_log(self, test_log_id):\n    pass\n",
                "\ndef create_test_log(self, test_log_id):\n    pass\n",
            ),
        ],
    )
    def test_remove_decorator(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.remove_decorator()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            ("self.assert_equal(len(listA), 5)", "self.assertEqual(len(listA), 5)"),
            ("self.assert_false(len(listA), 5)", "self.assertFalse(len(listA), 5)"),
            ("self.assert_true(len(listA), 5)", "self.assertTrue(len(listA), 5)"),
        ],
    )
    def test_convert_assert(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.convert_assert()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize("input_code, expected_code", [(tst_code.taut_code, tst_code.result_code)])
    def test_log_abcdxtl(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.in_memory = True
        subject.replace_log_compxtl('abcd')
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize("input_code, insert_code", [(tst_insert.input_code, tst_insert.insert_code)])
    def test_insert_class(self, input_code, insert_code, mocker):
        subject = self._create(mocker, input_code)
        subject.insert_class()
        result = subject.apply_to_string()
        assert_that(result, is_(input_code + insert_code))

    @pytest.mark.parametrize("input_code, expected_code", [(tst_class.set_up, tst_class.new_set_up)])
    def test_setup(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.convert_setup()
        result = subject.apply_to_string()
        assert result == expected_code

    @pytest.mark.parametrize("input_code, expected_code", [(tst_class.tear_down, tst_class.new_tear_down)])
    def test_teardown(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.refactor_teardown()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize("input_code, expected_code", [(tst_testdoubles.test_doubles_fun, tst_testdoubles.test_doubles_fun_new)])
    def test_testdoubles_fun(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.refactor_testdoubles_fun()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize("input_code, expected_code", [(tst_testdoubles.test_doubles_class, tst_testdoubles.test_doubles_class_new)])
    def test_testdoubles_class(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.refactor_testdoubles_class()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            ("@mock.patch('arg')\ndef test():\n    pass\n", "@patch('arg')\ndef test():\n    pass\n"),
            ("a = mock.patch(arg)", "a = mock.patch(arg)")
        ],
    )
    def test_remove_mock(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.replace_mock()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    def test_remove_stubserver(self, mocker):
        subject = self._create(mocker, "@TAUT.StubServer\ndef test():\n    pass\n")
        expected_code = "\ndef test():\n    pass\n"
        subject.remove_stubserver()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            ("self.tds.append(TestDoubles(mode, emr=self.emr))", "self.add_patcher(mode, 'emr', self.emr)"),
            ("self.tds.append(TestDoubles(a=ImprovedStub(b)))", "self.a = ImprovedStub(b)")
        ],
    )
    def test_convert_tds(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.convert_tds()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))


import textwrap
from pathlib import Path

import pytest
from hamcrest import ends_with, assert_that, is_

import targets
from renaissance.impl.types import Name
from renaissance.refactoring.taut2pyunit import Taut2Pyunit
import test_data.test_class as tst_class
import test_data.test_code as tst_code
import test_data.test_insert as tst_insert
from renaissance.impl.python.rst_node import PythonRstNode
import test_data.test_testdoubles as tst_testdoubles
from renaissance.utils.ast_utils import traverse


class TestTaut2Unittest:

    def test_init(self):
        subject = Taut2Pyunit(Path(targets.__file__).parent / "taut/taut_test.py")
        assert_that(subject.filename, ends_with("taut_test.py"))

    def _create(self, mocker, text) -> Taut2Pyunit:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code),
        )
        subject = Taut2Pyunit("x.py")
        subject.in_memory = True
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
                # try/except removed; other imports present → prepend before first import
                "import pytest\ntry:\n    import testoob as unittest\nexcept ImportError:\n    import unittest\nimport mock\n",
                "import unittest\nimport pytest\nimport mock\n",
            ),
            (
                # try/except removed; other imports present → prepend before first import
                "try:\n    import testoob as unittest\nexcept ImportError:\n    import unittest\nimport mock\n",
                "\nimport unittest\nimport mock\n",
            ),
            (
                # try/except removed; other imports present → prepend before first import
                "class Foo:\n    pass\ntry:\n    import testoob as unittest\nexcept ImportError:\n    import unittest\n",
                "import unittest\nclass Foo:\n    pass\n",
            ),
            (
                # try/except removed; import unittest already present → not duplicated
                "import unittest\ntry:\n    import testoob as unittest\nexcept ImportError:\n    import unittest\nimport mock\n",
                "import unittest\nimport mock\n",
            ),
            (
                # try/except only content; no other imports → prepend before first code node
                "try:\n    import testoob as unittest\nexcept ImportError:\n    import unittest\nclass MyTest:\n    pass\n",
                "\nimport unittest\nclass MyTest:\n    pass\n",
            ),
        ],
    )
    def test_remove_testoob_import(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.remove_testoob_import()
        subject.ensure_unittest_import(always=True)
        subject.commit()
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

    @pytest.mark.parametrize(
        "input_code, expected_code, indent",
        [
            (tst_testdoubles.test_indent, tst_testdoubles.test_indent_new, ""),
            (tst_testdoubles.test_indent_fun, tst_testdoubles.test_indent_fun_new, "    "),
        ],
    )
    def test_indentation(self, input_code, expected_code, indent, mocker):
        subject = self._create(mocker, input_code)
        subject.move_indent(indent)
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
        subject.replace_log_compxtl("abcd")
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

    def test_teardown(self, mocker):
        subject = self._create(mocker, tst_class.tear_down_simple)
        subject.convert_teardown()
        result = subject.apply_to_string()
        assert result == tst_class.tear_down_simple_new

    @pytest.mark.parametrize("input_code, expected_code", [(tst_class.tear_down, tst_class.new_tear_down)])
    def test_teardown_refactor(self, input_code, expected_code, mocker):
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
            ("a = mock.patch(arg)", "a = mock.patch(arg)"),
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
            ("self.tds.append(TestDoubles(a=ImprovedStub(b)))", "self.a = ImprovedStub(b)"),
        ],
    )
    def test_convert_tds(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.convert_tds()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            ("assert_double_equal(l.x, 0.0)", "self.assert_double_equal(l.x, 0.0)"),
            ("def a():\n    assert_double_equal(l.x, 0.0)", "def a():\n    self.assert_double_equal(l.x, 0.0)"),
        ],
    )
    def test_assert_doubles(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        [subject.replace("self." + node.name, node, False, False)
            for node in traverse(subject.node)
            if isinstance(node.ast_type(), Name) and node.name == "assert_double_equal"
        ]
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    def test_import_verify(self, mocker):
        subject = self._create(mocker, "def test_import(self):\n    self.import_and_verify_module('ABCDxTL')")
        expected_code = "def test_import(self):\n    import ABCDxTL\n    self.assertIsNotNone(ABCDxTL)"
        subject.convert_import_verify()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    def test_insert_asserter(self, mocker):
        subject = self._create(mocker, "def assert_double_equal(a, br=c):\n    pass")
        expected_code = tst_insert.insert_code
        subject.insert_asserter()
        subject.remove_assert_func()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    def test_replace_unittest_asserter(self, mocker):
        subject = self._create(mocker, "class A(TAUT.TestCase):\n    def b(self):\n        self.assert_raises(a, b=c)")
        expected_code = "class A(Asserter):\n    def b(self):\n        self.assert_raises(a, b=c)"
        subject.replace_unittest_with_asserter()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, expected_code",
        [
            ("assert_raises", "self.assert_raises"),
            ("assert_double_equal", "self.assert_double_equal"),
        ],
    )
    def test_assert_func(self, mocker, input_code, expected_code):
        subject = self._create(mocker, input_code)
        subject.assert_func()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    def test_convert_testdoubles_func(self, mocker):
        subject = self._create(mocker, tst_testdoubles.test_taut_doubles_class)
        subject.convert_testdoubles_fun()
        result = subject.apply_to_string()
        assert_that(result, is_(tst_testdoubles.test_taut_doubles_class_new))
        
    def test_convert_testdoubles_func_single_line(self, mocker):
        subject = self._create(mocker, tst_testdoubles.test_taut_doubles_class_single_line)
        subject.convert_testdoubles_fun()
        result = subject.apply_to_string()
        assert_that(result, is_(tst_testdoubles.test_taut_doubles_class_single_line_new))

    def test_setup_common(self, mocker):
        subject = self._create(mocker, tst_class.set_up_common)
        subject.convert_setup_common()
        result = subject.apply_to_string()
        assert_that(result, is_(tst_class.set_up_common_new))

    def test_teardown_common(self, mocker):
        subject = self._create(mocker, tst_class.tear_down_common)
        subject.convert_teardown_common()
        result = subject.apply_to_string()
        assert_that(result, is_(tst_class.tear_down_common_new))

    def test_add_patcher(self, mocker):
        subject = self._create(mocker, tst_class.tear_down_common_new)
        subject.convert_add_patcher()
        result = subject.apply_to_string()
        assert_that(result, is_(tst_class.tear_down_common_new + tst_class.insert_add_patcher + "\n"))

    def test_shared_setup(self, mocker):
        subject = self._create(mocker, "class A():\n    def sharedSetUp(self):\n        pass")
        expected_code = "class A():\n    def setUp(self):\n        pass"
        subject.shared_setup()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    def test_with_testdoubles(self, mocker):
        subject = self._create(mocker, "with TAUT.TestDoubles(module=mod, b=c):\n    pass")
        expected_code = "with patch.object(mod, 'b', c):\n    pass"
        subject.with_testdoubles()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    def test_insert_patch_import(self, mocker):
        subject = self._create(mocker, "import unittest\nself.patches = []")
        expected_code = (
            "import unittest\ntry:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\nself.patches = []"
        )
        subject.insert_patch_import()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    @pytest.mark.parametrize(
        "input_code, always, expected_code",
        [
            ("class MyTest(unittest.TestCase):\n    pass\n", False, "import unittest\nclass MyTest(unittest.TestCase):\n    pass\n"),
            ("class MyTest:\n    pass\n", False, "class MyTest:\n    pass\n"),
            ("import unittest\nclass MyTest(unittest.TestCase):\n    pass\n", False, "import unittest\nclass MyTest(unittest.TestCase):\n    pass\n"),
            ("import unittest\nclass MyTest(unittest.TestCase):\n    pass\n", True, "import unittest\nclass MyTest(unittest.TestCase):\n    pass\n"),
            ("class MyTest:\n    pass\n", True, "import unittest\nclass MyTest:\n    pass\n"),
        ],
    )
    def test_ensure_unittest_import(self, input_code, always, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.ensure_unittest_import(always=always)
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

    # Intent: prevent regression on case where whitespace in empty lines is removed internally in rewriter.
    # The start and end offsets within the node object stay the same, so the rewriter would replace a wrong segment.
    @pytest.mark.parametrize("input_code, expected_code", [(tst_testdoubles.test_taut_testcase_with_whitespace_on_empty_line, 
                                                            tst_testdoubles.test_taut_testcase_with_whitespace_on_empty_line_output)])
    def test_rewriter_handles_whitespace_on_empty_line(self, input_code, expected_code, mocker):
        subject = self._create(mocker, input_code)
        subject.replace_taut()
        result = subject.apply_to_string()
        assert_that(result, is_(expected_code))

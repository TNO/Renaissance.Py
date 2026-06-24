import textwrap

from hamcrest import assert_that, contains_string, is_

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.python_refactoring import PythonRefactoring


class TestPythonRefactoring:

    def _patch_factory(self, mocker, text="pass", filename="test_foo.py"):
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code, filename),
        )

    # ------------------------------------------------------------------
    # __init__ / replace_stmt
    # ------------------------------------------------------------------

    def test_init_sets_default_list_patterns(self, mocker):
        self._patch_factory(mocker)
        from renaissance.refactoring.unit2pytest import Unit2Pytest

        subject = Unit2Pytest("test_foo.py")
        # base class defaults are overridden by subclass, but they are set in __init__
        assert_that(subject.black_list_pattern, is_("utils_for_test"))
        assert_that(subject.white_list_pattern, is_("test"))

    def test_replace_stmt_rewrites_matching_pattern(self, mocker):
        self._patch_factory(
            mocker,
            """
            import unittest
            """,
            "test_foo.py",
        )
        from renaissance.refactoring.unit2pytest import Unit2Pytest

        subject = Unit2Pytest("test_foo.py")
        subject.in_memory = True
        subject.replace_stmt("import unittest", "import pytest\nfrom hamcrest import *")
        assert_that(subject.apply_to_string(), contains_string("import pytest"))
        assert_that(subject.apply_to_string(), contains_string("from hamcrest import *"))

    def test_replace_stmt_expands_variadic_captures(self, mocker):
        self._patch_factory(
            mocker,
            """
            from unittest import TestCase, skip
            """,
            "test_foo.py",
        )
        from renaissance.refactoring.unit2pytest import Unit2Pytest

        subject = Unit2Pytest("test_foo.py")
        subject.in_memory = True
        subject.replace_stmt(
            "from unittest import TestCase,$$symbols",
            "import pytest\nfrom hamcrest import *",
        )
        assert_that(subject.apply_to_string(), contains_string("import pytest"))

    # ------------------------------------------------------------------
    # process() — skip branch
    # ------------------------------------------------------------------

    def test_process_skips_file_matching_black_list(self, mocker, capsys):
        self._patch_factory(mocker, "pass", "utils_for_test_foo.py")
        run_spy = mocker.patch("renaissance.refactoring.unit2pytest.Unit2Pytest.run")
        PythonRefactoring.process("Unit2Pytest", "utils_for_test_foo.py")
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("skipping"))
        assert_that(run_spy.call_count, is_(0))

    def test_process_skips_file_not_matching_white_list(self, mocker, capsys):
        self._patch_factory(mocker, "pass", "my_module.py")
        run_spy = mocker.patch("renaissance.refactoring.unit2pytest.Unit2Pytest.run")
        PythonRefactoring.process("Unit2Pytest", "my_module.py")
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("skipping"))
        assert_that(run_spy.call_count, is_(0))

    # ------------------------------------------------------------------
    # process() — run branch
    # ------------------------------------------------------------------

    def test_process_runs_refactor_on_matching_file(self, mocker, capsys):
        self._patch_factory(mocker, "pass", "test_foo.py")
        run_spy = mocker.patch("renaissance.refactoring.unit2pytest.Unit2Pytest.run")
        PythonRefactoring.process("Unit2Pytest", "test_foo.py")
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("refactor"))
        assert_that(run_spy.call_count, is_(1))

    # ------------------------------------------------------------------
    # body property
    # ------------------------------------------------------------------

    def test_body_returns_module_level_statements(self, mocker):
        self._patch_factory(
            mocker,
            """
            x = 1
            y = 2
            """,
            "test_foo.py",
        )
        from renaissance.refactoring.unit2pytest import Unit2Pytest

        subject = Unit2Pytest("test_foo.py")
        assert_that(len(subject.body), is_(2))

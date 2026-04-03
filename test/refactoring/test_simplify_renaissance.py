import textwrap

import pytest
from hamcrest import assert_that, contains_string, ends_with, is_, not_

from renaissance.impl.python import PythonRstNode
from renaissance.refactoring.simplify_renaissance import SimplifyRenaissance


class TestSimplifyRenaissance:

    def _create(self, mocker, text) -> SimplifyRenaissance:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code, "unit2pytest.py"),
        )
        subject = SimplifyRenaissance("unit2pytest.py")
        subject.in_memory = True
        return subject

    def test_init_sets_white_and_black_list(self, mocker):
        subject = self._create(mocker, "pass")
        assert_that(subject.white_list_pattern, is_("unit2pytest"))
        assert_that(subject.black_list_pattern, is_("SimplifyRenaissance"))

    def test_run_skips_file_matching_black_list(self, mocker, capsys):
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text("pass"),
        )
        subject = SimplifyRenaissance("SimplifyRenaissance.py")
        subject.in_memory = True
        subject.run()
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("skipping"))

    def test_run_skips_file_not_matching_white_list(self, mocker, capsys):
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text("pass"),
        )
        subject = SimplifyRenaissance("other_module.py")
        subject.in_memory = True
        subject.run()
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("skipping"))

    def test_run_rewrites_expansion_signature_access(self, mocker):
        subject = self._create(mocker, """
            def foo():
                val = match.expansions["$key"][0].signature
            """)
        subject.run()
        assert_that(subject.apply_to_string(), contains_string('val= match["$key"]'))
        assert_that(subject.apply_to_string(), not_(contains_string(".expansions")))

    def test_run_rewrites_factory_create_from_text(self, mocker):
        subject = self._create(mocker, """
            def foo():
                factory = ASTFactory(PythonASTNode)
                atu = factory.create_from_text(code, name)
            """)
        subject.run()
        assert_that(subject.apply_to_string(), contains_string("PythonASTNode.load_from_text(code, name)"))
        assert_that(subject.apply_to_string(), not_(contains_string("ASTFactory")))

    def test_run_processes_matching_file(self, mocker, capsys):
        subject = self._create(mocker, "pass")
        subject.run()
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("simplify"))


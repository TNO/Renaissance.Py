import textwrap

import pytest
from hamcrest import assert_that, is_
from renaissance.impl.python.python_ast_node import PythonASTNode
from renaissance.refactoring.python_refactoring import PythonRefactoring


class TestRefactorWithRewrite:

    def _create(self, mocker, text) -> PythonRefactoring:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.syntax_tree.ast_factory.ASTFactory.create",
            return_value=PythonASTNode.load_from_text(code),
        )
        subject = PythonRefactoring("x.py")
        return subject

    @pytest.mark.skip("failing on white space and comments")
    def test_convert_plain_assert_same_length_rewrites_to_has_length(self, mocker):
        refactoring = self._create(
            mocker,
            """
        def test_functions(self):
            # with comments to remove
            with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)):
                # comments to remove
                log = TAUT.Logger()    
                # comments to keep
                test_log_id = DDXA.Object('a')
                test_log = emrwxtl.create_test_log(test_log_id)
                
                file_id = DDXA.Object('b')
                file_name = DDXA.Object('c')
                test_log, version_mismatch = emrwxtl.retrieve_test_log(file_id, test_log_id, file_name)
                emrwxtl.store_test_log(file_id, test_log)
                # end comments to keep""",
        )
        with_stmts = refactoring.pattern_factory.create_statements(
            "with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)):\n  log = TAUT.Logger()\n  $$stmt"
        )
        refactoring.in_memory = True
        for match in refactoring.find_match(with_stmts):
            refactoring.replace(match["$$stmt"], match.nodes, True, True)

        refactoring.commit()
        assert_that(
            refactoring.apply_to_string(),
            is_(
                """
        def test_functions(self):
                # comments to keep
                test_log_id = DDXA.Object('a')
                test_log = emrwxtl.create_test_log(test_log_id)
                
                file_id = DDXA.Object('b')
                file_name = DDXA.Object('c')
                test_log, version_mismatch = emrwxtl.retrieve_test_log(file_id, test_log_id, file_name)
                emrwxtl.store_test_log(file_id, test_log)
                # end comments to keep"""
            ),
        )

    def test_refactor_replace_multi_placeholder(self, mocker):
        """
        test case showing a replacement of a multi placeholder
        that matches a non-empty list of AST nodes in the code
        """       
        refactoring = self._create(mocker, "def f(a):\n    f(2, 0)")
        function_call = refactoring.pattern_factory.create_expression("f($$params, 0)")
        refactoring.in_memory = True
        for match in refactoring.find_match(function_call):
            refactoring.replace(match["$$params"], "1")
        refactoring.commit()
        assert_that(refactoring.apply_to_string(), is_("def f(a):\n    f(1, 0)"))

    def test_refactor_replace_multi_placeholder_empty(self, mocker):
        """
        test case showing a replacement of a multi placeholder
        that matches an empty list of AST nodes in the code
        """
        # TODO: is this the behaviour we want?
        # Can $$params be empty and a comma absent, while present in the pattern.
        refactoring = self._create(mocker, "def f(a):\n    f(0)")
        function_call = refactoring.pattern_factory.create_expression("f($$params, 0)")
        refactoring.in_memory = True
        for match in refactoring.find_match(function_call):
            refactoring.replace(match["$$params"], "1, ")
        refactoring.commit()
        assert_that(refactoring.apply_to_string(), is_("def f(a):\n    f(1, 0)"))

    # TODO: make test case with a find and replacement pattern
    # find:  "f($$params, 0)"
    # replace: "f(1, $$params, 0)"
    # With $$params empty, we should get "f(1, 0)" so one comma only!
        
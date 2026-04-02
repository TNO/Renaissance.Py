import textwrap

import pytest
from hamcrest import assert_that, is_
from renaissance.impl.python.rst_node import PythonASTNode
from renaissance.refactoring.python_refactoring import PythonRefactoring


class TestRefactorWithRewrite:

    def _create(self,mocker,text) -> PythonRefactoring:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.syntax_tree.ast_factory.ASTFactory.create",
            return_value=PythonASTNode.load_from_text(code),
        )
        subject = PythonRefactoring("x.py")
        return subject

    # @pytest.mark.skip("failing on white space and comments")
    def test_convert_plain_assert_same_length_rewrites_to_has_length(self,mocker):
        refactoring = self._create(mocker, """
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
                # end comments to keep""")
        with_stmts = refactoring.pattern_factory.create_statements('with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)):\n  log = TAUT.Logger()\n  $$stmt')
        refactoring.in_memory = True
        for match in refactoring.find_match(with_stmts):
            refactoring.replace(match['$$stmt'], match.nodes,True, True)


        refactoring.commit()
        assert_that(refactoring.apply_to_string(), is_("""
        def test_functions(self):
                # comments to keep
                test_log_id = DDXA.Object('a')
                test_log = emrwxtl.create_test_log(test_log_id)
                
                file_id = DDXA.Object('b')
                file_name = DDXA.Object('c')
                test_log, version_mismatch = emrwxtl.retrieve_test_log(file_id, test_log_id, file_name)
                emrwxtl.store_test_log(file_id, test_log)
                # end comments to keep"""))

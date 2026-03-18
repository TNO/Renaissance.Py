import textwrap

import pytest
from black import Path
from hamcrest import assert_that, contains_string, has_length, is_, not_

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.refactoring.unit2pytest import  Unit2Pytest
from renaissance.syntax_tree import ASTRewriter, ASTFactory
from renaissance.syntax_tree.match_finder import match_pattern


class TestUnit2pytest:
    def test_cant_find_parameterized(self):
        code = textwrap.dedent('''
        from parameterized import parameterized
    
        class TestASTReference:
    
            @parameterized.expand(Factories.extend())
            def test_definition_declaration_references(self, _, factory, code, *args):
                pass
        ''')
        factory = ASTFactory(PythonASTNode, [])
        pattern_factory = PythonPatternFactory(factory, None)
        atu = PythonASTNode.load_from_text(code)
        unittest = pattern_factory.create_statements(
            '@parameterized.expand($$parameters)\ndef $fun($$args, *$$vargs):\n    $$stmts')
        found = match_pattern(atu.children, unittest)
        assert_that(found , has_length(1))


    def test_convert_multiple_stmts(self, mocker):
        code = textwrap.dedent('''
        def test_asert():
            results = ['1']
            count: int = len(results)
            assert 1 == count, "count = " + str(count)
        ''')
        mocker.patch("renaissance.syntax_tree.ast_factory.ASTFactory.create", return_value=PythonASTNode.load_from_text(code))

        expected = textwrap.dedent('''
        def test_asert():
            results = ['1']
            assert_that(results, has_length(1), f"length of results = {len(results)}")
        ''')

        subject = Unit2Pytest('file.py')
        subject.convert_plain_assert_same_length()
        assert_that(subject.rewriter.apply_to_string(), is_(expected))


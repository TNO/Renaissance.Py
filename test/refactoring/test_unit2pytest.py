import textwrap

import pytest
from black import Path
from hamcrest import assert_that, contains_string, has_length

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTRewriter, ASTFactory
from renaissance.syntax_tree.match_finder import match_pattern


def test_cant_find_parameterized():
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
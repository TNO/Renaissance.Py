import ast
from unittest.mock import patch

from hypothesis import given, settings, assume
import hypothesmith

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.typevar_check import TypeVarCheck


class TestTypeVarCheckProperties:

    @given(source=hypothesmith.from_grammar())
    @settings(max_examples=50, deadline=None)
    def test_never_crashes(self, source):
        try:
            ast.parse(source)
        except SyntaxError:
            assume(False)
            return
    
        with patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(source),
        ):
            subject = TypeVarCheck("x.py")
            subject.in_memory = True
            subject.find_multi_scope_typevars()

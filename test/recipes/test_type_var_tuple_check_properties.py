"""Property-based tests for TypeVarTupleCheck's detection and fix passes."""

import ast
from unittest.mock import patch

import hypothesmith
from hypothesis import assume, given, settings

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.type_var_tuple_check import TypeVarTupleCheck


class TestTypeVarTupleCheckProperties:
    """See module docstring."""

    @given(source=hypothesmith.from_grammar())
    @settings(max_examples=50, deadline=None)
    def test_never_crashes(self, source: str) -> None:
        """AI: Verify find_legacy_unpack_usage never raises on arbitrary hypothesmith-generated valid Python source."""
        try:
            ast.parse(source)
        except SyntaxError:
            assume(False)

        with patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(source),
        ):
            subject = TypeVarTupleCheck("x.py")
            subject.in_memory = True
            subject.find_legacy_unpack_usage()

    @given(source=hypothesmith.from_grammar())
    @settings(max_examples=50, deadline=None)
    def test_fix_never_crashes(self, source: str) -> None:
        """AI: Verify fix_legacy_unpack_usage never raises on arbitrary hypothesmith-generated valid Python source."""
        try:
            ast.parse(source)
        except SyntaxError:
            assume(False)

        with patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(source),
        ):
            subject = TypeVarTupleCheck("x.py")
            subject.in_memory = True
            subject.min_python = (3, 11)
            subject.fix_legacy_unpack_usage()

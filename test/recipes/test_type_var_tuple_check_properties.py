import ast
from unittest.mock import patch

import hypothesmith
from hypothesis import assume, given, settings

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.type_var_tuple_check import TypeVarTupleCheck


class TestTypeVarTupleCheckProperties:

    @given(source=hypothesmith.from_grammar())
    @settings(max_examples=50, deadline=None)
    def test_never_crashes(self, source: str) -> None:
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

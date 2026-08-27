import ast
from unittest.mock import patch

from hamcrest import assert_that, is_
from hypothesis import given, settings, assume, strategies as st
import hypothesmith

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.type_var_check import TypeVarCheck


@st.composite
def source_with_typevars(draw: st.DrawFn) -> tuple[str, set[str]]:
    """Build Python source that always declares at least one TypeVar.

    Unlike `hypothesmith.from_grammar()`, this controls exactly how many
    functions use each TypeVar, so the expected multi-scope names are known
    up front instead of left to chance.
    """
    names = draw(st.lists(st.sampled_from(["T", "U", "V"]), min_size=1, max_size=3, unique=True))

    lines: list[str] = []
    expected: set[str] = set()
    for i, name in enumerate(names):
        num_funcs = draw(st.integers(min_value=1, max_value=3))
        for j in range(num_funcs):
            lines.append(f"def f{i}_{j}(x: {name}) -> {name}:\n    return x\n")
        if num_funcs >= 2:
            expected.add(name)
        lines.append(f'{name} = TypeVar("{name}")\n')

    return "\n".join(lines), expected


class TestTypeVarCheckProperties:
    @given(source=hypothesmith.from_grammar())
    @settings(max_examples=50, deadline=None)
    def test_never_crashes(self, source: str) -> None:
        try:
            ast.parse(source)
        except SyntaxError:
            assume(False)

        with patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(source),
        ):
            subject = TypeVarCheck("x.py")
            subject.in_memory = True
            subject.find_multi_scope_typevars()

    @given(data=source_with_typevars())
    @settings(max_examples=50, deadline=None)
    def test_detects_exactly_the_multi_scope_typevars(self, data: tuple[str, set[str]]) -> None:
        source, expected = data

        with patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(source),
        ):
            subject = TypeVarCheck("x.py")
            subject.in_memory = True
            result = subject.find_multi_scope_typevars()

        assert_that(set(result.keys()), is_(expected))

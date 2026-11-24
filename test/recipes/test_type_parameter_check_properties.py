# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Property-based tests for the TypeParameterCheck phases on generated modules."""

import ast
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple
from unittest.mock import patch

import pytest
from hamcrest import assert_that, equal_to
from hypothesis import example, given, settings
from hypothesis import strategies as st

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.recipes.type_parameter_check import TypeParameterCheck

if TYPE_CHECKING:
    from collections.abc import Callable


class _Declaration(NamedTuple):
    """A module-level type parameter declaration and a parameter that uses it."""

    constructor: str
    statement: str
    parameter: str


_DECLARATIONS = {
    "T": _Declaration("TypeVar", 'T = TypeVar("T")', "x: T"),
    "B": _Declaration("TypeVar", 'B = TypeVar("B", bound=int)', "x: B"),
    "D": _Declaration("TypeVar", 'D = TypeVar("D", default=int)', "x: D"),
    "P": _Declaration("ParamSpec", 'P = ParamSpec("P")', "f: Callable[P, int]"),
    "Ts": _Declaration("TypeVarTuple", 'Ts = TypeVarTuple("Ts")', "*args: *Ts"),
}
_PLAIN_PARAMETER = "x: int"

_PHASES = [
    pytest.param(TypeParameterCheck.check, id="check"),
    pytest.param(TypeParameterCheck.convert_declared_typevars, id="convert"),
    pytest.param(TypeParameterCheck.remove_orphaned_declarations, id="orphaned"),
]


@st.composite
def modules(draw: st.DrawFn, *, with_declarations: bool = True) -> str:
    """Draw a module of type parameter declarations, functions using them, and optionally a plain and a generic class."""
    names = draw(st.lists(st.sampled_from(sorted(_DECLARATIONS)), max_size=3, unique=True)) if with_declarations else []
    parameters = [_DECLARATIONS[name].parameter for name in names] or [_PLAIN_PARAMETER]
    generic_class = "T" in names and draw(st.booleans())

    typing_names = {_DECLARATIONS[name].constructor for name in names} | ({"Generic"} if generic_class else set[str]())
    imports = [f"from typing import {', '.join(sorted(typing_names))}"] if typing_names else []
    if "P" in names:
        imports.insert(0, "from collections.abc import Callable")

    blocks = ["\n".join(imports)] if imports else []
    if names:
        blocks.append("\n".join(_DECLARATIONS[name].statement for name in names))
    blocks.extend(
        f"def f{index}({parameter}) -> None:\n    pass"
        for index, parameter in enumerate(draw(st.lists(st.sampled_from(parameters), max_size=4)))
    )
    if draw(st.booleans()):
        blocks.append(f"class Plain:\n    def method(self, {draw(st.sampled_from(parameters))}) -> None:\n        pass")
    if generic_class:
        blocks.append("class Box(Generic[T]):\n    def get(self, x: T) -> T:\n        return x")
    return "\n\n\n".join(blocks) + "\n" if blocks else ""


def _run(source: str, phase: Callable[[TypeParameterCheck], object]) -> str:
    """Run one phase of TypeParameterCheck on source in memory and return the rewritten text."""
    with patch(
        "renaissance.integrations.python.ast.factory.PythonFactory.create",
        return_value=PythonCstNode.load_from_text(source, "x.py"),
    ):
        subject = TypeParameterCheck(Path("x.py"))
        subject.in_memory = True
        phase(subject)
        return subject.apply_to_string()


class TestTypeParameterCheckProperties:
    """Properties every phase must have on any module, whatever it converts or removes."""

    @pytest.mark.parametrize("phase", _PHASES)
    @settings(max_examples=50, deadline=None)
    @given(source=modules())
    @example(source="")
    def test_output_parses_and_a_second_run_changes_nothing(self, phase: Callable[[TypeParameterCheck], object], source: str) -> None:
        """The phase leaves valid Python, and running it again on that result changes nothing."""
        once = _run(source, phase)

        ast.parse(once)
        assert_that(_run(once, phase), equal_to(once))

    @pytest.mark.parametrize("phase", _PHASES)
    @settings(max_examples=50, deadline=None)
    @given(source=modules(with_declarations=False))
    def test_module_without_type_parameters_is_left_unchanged(self, phase: Callable[[TypeParameterCheck], object], source: str) -> None:
        """A module that declares no type parameter comes out identical."""
        assert_that(_run(source, phase), equal_to(source))

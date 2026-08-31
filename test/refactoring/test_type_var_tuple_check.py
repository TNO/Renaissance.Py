"""Tests for the TypeVarTupleCheck recipe."""

from collections.abc import Callable
from typing import cast

import pytest
from hamcrest import assert_that, contains_inanyorder, empty

from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.refactoring.type_var_tuple_check import TypeVarTupleCheck


class TestTypeVarTupleCheck:
    """See module docstring."""

    @pytest.mark.parametrize("code,expected", [
        (
            """
            from typing import TypeVarTuple, Generic, Unpack
            Ts = TypeVarTuple("Ts")
            class Foo(Generic[Unpack[Ts]]):
                pass
            """,
            ["Ts"],
        ),
        (
            """
            from typing import TypeVarTuple
            Ts = TypeVarTuple("Ts")
            def foo(*args: *Ts) -> tuple[*Ts]:
                return args
            """,
            [],
        ),
        (
            """
            def foo(x: int) -> int:
                return x
            """,
            [],
        ),
    ])
    def test_legacy_unpack_usage(
        self, make_recipe: Callable[[type[PythonRefactoring], str], PythonRefactoring], code: str, expected: list[str]
    ) -> None:
        subject = cast(TypeVarTupleCheck, make_recipe(TypeVarTupleCheck, code))
        result = subject.find_legacy_unpack_usage()
        if expected:
            assert_that(result, contains_inanyorder(*expected))
        else:
            assert_that(result, empty())

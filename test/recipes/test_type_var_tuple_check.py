"""Tests for the TypeVarTupleCheck recipe."""

from collections.abc import Callable
from typing import cast

import pytest
from hamcrest import assert_that, contains_inanyorder, empty, is_

from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.type_var_tuple_check import TypeVarTupleCheck


class TestTypeVarTupleCheck:
    """See module docstring."""

    @pytest.mark.parametrize(
        "code,expected",
        [
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
        ],
    )
    def test_legacy_unpack_usage(
        self, make_recipe: Callable[[type[PythonRefactoring], str], PythonRefactoring], code: str, expected: list[str]
    ) -> None:
        """AI: Verify find_legacy_unpack_usage finds only TypeVarTuples used via the legacy Unpack[] form."""
        subject = cast(TypeVarTupleCheck, make_recipe(TypeVarTupleCheck, code))
        result = subject.find_legacy_unpack_usage()
        if expected:
            assert_that(result, contains_inanyorder(*expected))
        else:
            assert_that(result, empty())

    @pytest.mark.parametrize(
        ("min_python", "expected"),
        [
            pytest.param(None, False, id="unknown"),
            pytest.param((3, 10), False, id="3.10"),
            pytest.param((3, 11), True, id="3.11"),
            pytest.param((3, 12), True, id="3.12"),
        ],
    )
    def test_pep646_gate_threshold(
        self,
        create_type_var_tuple_check: Callable[[str], TypeVarTupleCheck],
        min_python: tuple[int, int] | None,
        *,
        expected: bool,
    ) -> None:
        """The PEP 646 gate opens only for a known min_python of 3.11 or later."""
        subject = create_type_var_tuple_check("x = 1")
        subject.min_python = min_python

        assert_that(subject._target_supports_pep646(), is_(expected))  # noqa: SLF001

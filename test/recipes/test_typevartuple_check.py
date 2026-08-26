import textwrap

import pytest
from hamcrest import assert_that, contains_inanyorder, empty
from pytest_mock import MockerFixture

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.typevartuple_check import TypeVarTupleCheck


class TestTypeVarTupleCheck:
    def _create(self, mocker: MockerFixture, text: str) -> TypeVarTupleCheck:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code),
        )
        subject = TypeVarTupleCheck("x.py")
        subject.in_memory = True
        return subject

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
    def test_legacy_unpack_usage(self, mocker: MockerFixture, code: str, expected: list[str]) -> None:
        subject = self._create(mocker, code)
        result = subject.find_legacy_unpack_usage()
        if expected:
            assert_that(result, contains_inanyorder(*expected))
        else:
            assert_that(result, empty())

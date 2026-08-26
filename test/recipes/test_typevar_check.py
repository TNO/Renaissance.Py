import textwrap
import pytest
from hamcrest import assert_that, has_key, is_not  # pyright: ignore[reportUnknownVariableType]
from pytest_mock import MockerFixture
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.typevar_check import TypeVarCheck

class TestTypeVarCheck:

    def _create(self, mocker: MockerFixture, text: str) -> TypeVarCheck:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code),
        )
        subject = TypeVarCheck("x.py")
        subject.in_memory = True
        return subject

    def test_typevar_used_in_multiple_functions(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
            class Foo:
                def a(self: T) -> T:
                    return self
                def b(self: T) -> T:
                    return self

            T = TypeVar("T")
        """)
        result = subject.find_multi_scope_typevars()
        assert_that(result, has_key("T"))

    def test_typevar_used_in_single_function_not_flagged(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)
        result = subject.find_multi_scope_typevars()
        assert_that(result, is_not(has_key("T")))

    @pytest.mark.parametrize("code,name,should_flag", [
        (
            """
            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y
            def c(z: T) -> T:
                return z

            T = TypeVar("T")
            """,
            "T",
            True,
        ),
        (
            """
            def a(x: T, y: T) -> T:
                return x

            T = TypeVar("T")
            """,
            "T",
            False,
        ),
        (
            """
            def a(x: T) -> T:
                return x
            def b(y: U) -> U:
                return y
            def c(z: U) -> U:
                return z

            T = TypeVar("T")
            U = TypeVar("U")
            """,
            "T",
            False,
        ),
        (
            """
            def a(x: T) -> T:
                return x
            def b(y: U) -> U:
                return y
            def c(z: U) -> U:
                return z

            T = TypeVar("T")
            U = TypeVar("U")
            """,
            "U",
            True,
        ),
        (
            """
            def a(x: int) -> int:
                return x
            """,
            "T",
            False,
        ),
        (
            """
            def a(x: P) -> P:
                return x
            def b(y: P) -> P:
                return y
            def c(z: P) -> P:
                return z

            P = ParamSpec("P")
            """,
            "P",
            True,
        ),
        (
            """
            def a(*args: *Ts) -> tuple[*Ts]:
                return args
            def b(*args: *Ts) -> tuple[*Ts]:
                return args

            Ts = TypeVarTuple("Ts")
            """,
            "Ts",
            True,
        )
    ])
    def test_multi_scope_detection_cases(self, mocker: MockerFixture, code: str, name: str, should_flag: bool) -> None:
        subject = self._create(mocker, code)
        result = subject.find_multi_scope_typevars()
        if should_flag:
            assert_that(result, has_key(name))
        else:
            assert_that(result, is_not(has_key(name)))
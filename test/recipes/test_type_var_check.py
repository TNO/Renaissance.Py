"""Whole-class TypeVarCheck concerns not owned by a single phase.

Multi-scope detection, end-to-end check(), and the PEP 695 version gate.
"""

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest
from hamcrest import assert_that, contains_string, has_entry, has_key, is_, is_not, not_
from pytest_mock import MockerFixture

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.type_var_check import TypeVarCheck, target_supports_pep695


class TestTypeVarCheck:
    """See module docstring."""

    def test_typevar_used_in_multiple_functions(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        subject = create_type_var_check("""
            class Foo:
                def a(self: T) -> T:
                    return self
                def b(self: T) -> T:
                    return self

            T = TypeVar("T")
        """)
        result = subject.find_multi_scope_typevars()
        assert_that(result, has_key("T"))

    def test_typevar_used_in_single_function_not_flagged(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        subject = create_type_var_check("""
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
    def test_multi_scope_detection_cases(
        self, create_type_var_check: Callable[[str], TypeVarCheck], code: str, name: str, should_flag: bool
    ) -> None:
        subject = create_type_var_check(code)
        result = subject.find_multi_scope_typevars()
        if should_flag:
            assert_that(result, has_key(name))
        else:
            assert_that(result, is_not(has_key(name)))

    def test_check_cleans_up_ruff_style_leftover_end_to_end(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        # Caught directly by phase 2 (convert_declared_typevars skips the already-shadowed
        # function and just drops the now-redundant declaration) - "orphaned" (phase 3) is
        # a defensive no-op here, exercised separately by test_type_var_check_orphaned.py.
        subject = create_type_var_check("""
            from typing import TypeVar
            T = TypeVar('T')

            def b[T](x: T) -> T:
                return x
        """)
        subject.run()

        assert_that(subject.result["converted"], has_entry("T", "fixed"))
        assert_that(subject.result["orphaned"], is_({}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))
        assert_that(output, not_(contains_string("TypeVar")))

    def _create_versioned(
        self, mocker: MockerFixture, tmp_path: Path, requires_python: str | None, code: str
    ) -> TypeVarCheck:
        if requires_python is not None:
            (tmp_path / "pyproject.toml").write_text(f'[project]\nrequires-python = "{requires_python}"\n')
        file_path = str(tmp_path / "subject.py")
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(textwrap.dedent(code), file_path),
        )
        subject = TypeVarCheck(file_path)
        subject.in_memory = True
        return subject

    # target_supports_pep695() is a thin wrapper around minimum_python_version() (see
    # test/utils/test_python_version.py for the deep coverage of pyproject.toml lookup and
    # requires-python parsing) - these two just confirm it applies the >=(3, 12) threshold.
    def test_target_supports_pep695_true_for_3_12_plus(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.12"\n')
        assert_that(target_supports_pep695(str(tmp_path / "file.py")), is_(True))

    def test_target_supports_pep695_false_for_3_10(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.10"\n')
        assert_that(target_supports_pep695(str(tmp_path / "file.py")), is_(False))

    def test_convert_declared_typevars_reports_unsafe_when_target_too_old(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        subject = self._create_versioned(mocker, tmp_path, ">=3.10", """
            from typing import TypeVar

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.apply_to_string(), contains_string('T = TypeVar("T")'))

    def test_convert_declared_typevars_still_fixes_when_target_new_enough(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        subject = self._create_versioned(mocker, tmp_path, ">=3.12", """
            from typing import TypeVar

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("def a[T](x: T) -> T:"))

    def test_check_still_localizes_when_target_too_old(self, mocker: MockerFixture, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.10"\n')
        (tmp_path / "file_1.py").write_text(textwrap.dedent("""
            from typing import TypeVar
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """))
        importing_file = str(tmp_path / "file_2.py")
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(
                textwrap.dedent("""
                    from file_1 import T
                    def b(x: T) -> T:
                        return x
                    """),
                importing_file,
            ),
        )
        subject = TypeVarCheck(importing_file)
        subject.in_memory = True
        subject.run()

        assert_that(subject.result["cross_file"], has_entry("T", "fixed"))
        assert_that(subject.result["converted"], has_entry("T", "unsafe"))
        output = subject.apply_to_string()
        assert_that(output, contains_string('T = TypeVar(\'T\')'))
        assert_that(output, not_(contains_string("def b[T]")))

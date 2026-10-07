"""Whole-class TypeVarCheck concerns not owned by a single phase.

End-to-end check(), including a target below the PEP 695 version gate.
"""

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entry, not_
from pytest_mock import MockerFixture

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.type_var_check import TypeVarCheck
from renaissance.recipes.type_var_domain import UnsafeReason


class TestTypeVarCheck:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("signature", "expected_converted"),
        [
            pytest.param("def b(x: T) -> T:", {"T": "fixed"}, id="legacy-signature"),
            pytest.param("def b[T](x: T) -> T:", {}, id="ruff-style-leftover"),
        ],
    )
    def test_check_converts_then_removes_the_declaration_end_to_end(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        signature: str,
        expected_converted: dict[str, str],
    ) -> None:
        """Verify check() adds the type parameter where missing, then removes the now-orphaned declaration."""
        subject = create_type_var_check(f"""
            from typing import TypeVar
            T = TypeVar('T')

            {signature}
                return x
        """)
        subject.run()

        assert_that(subject.result, equal_to({"cross_file": {}, "converted": expected_converted, "orphaned": {"T": "fixed"}}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))
        assert_that(output, not_(contains_string("T = TypeVar")))

    def test_check_converts_but_keeps_an_exported_declaration(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """Verify check() converts the functions but keeps a declaration listed in __all__, reporting why."""
        subject = create_type_var_check("""
            from typing import TypeVar
            __all__ = ["T"]
            T = TypeVar('T')

            def first(items: list[T]) -> T:
                return items[0]
        """)
        subject.run()

        assert_that(subject.result, equal_to({"cross_file": {}, "converted": {"T": "fixed"}, "orphaned": {"T": "unsafe"}}))
        assert_that(subject.orphaned_unsafe_reasons, equal_to({"T": UnsafeReason.DECLARED_TYPEVAR_EXPORTED}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def first[T](items: list[T]) -> T:"))
        assert_that(output, contains_string("T = TypeVar('T')"))

    def test_check_keeps_declaration_still_used_by_a_generic_class(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """Verify check() converts a standalone function but keeps the declaration a Generic[...] base still needs."""
        subject = create_type_var_check("""
            from typing import Generic, TypeVar
            T = TypeVar('T')

            class Box(Generic[T]):
                def get(self, x: T) -> T:
                    return x

            def first(items: list[T]) -> T:
                return items[0]
        """)
        subject.run()

        assert_that(subject.result, equal_to({"cross_file": {}, "converted": {"T": "fixed"}, "orphaned": {}}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def first[T](items: list[T]) -> T:"))
        assert_that(output, contains_string("T = TypeVar('T')"))
        assert_that(output, contains_string("    def get(self, x: T) -> T:"))

    def test_check_still_localizes_when_target_too_old(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify cross-file localization still runs when the target is too old for the PEP 695 conversion."""
        (tmp_path / "file_1.py").write_text(
            textwrap.dedent("""
            from typing import TypeVar
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """)
        )
        importing_file = str(tmp_path / "file_2.py")
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
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
        subject.min_python = (3, 10)
        subject.in_memory = True
        subject.run()

        assert_that(subject.result["cross_file"], has_entry("T", "fixed"))
        assert_that(subject.result["converted"], has_entry("T", "unsafe"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("T = TypeVar('T')"))
        assert_that(output, not_(contains_string("def b[T]")))

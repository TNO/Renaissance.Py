"""End-to-end tests for TypeVarCheck.check() across its phases."""

from collections.abc import Callable

import pytest
from hamcrest import assert_that, contains_string, equal_to, not_

from renaissance.recipes.type_var_check import TypeVarCheck


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

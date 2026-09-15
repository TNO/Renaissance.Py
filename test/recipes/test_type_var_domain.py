"""Tests for type_var_domain's safety predicates and their UnsafeReason results."""

import ast
import textwrap

import pytest
from hamcrest import assert_that, is_

from renaissance.recipes.type_var_domain import (
    UnsafeReason,
    find_type_param_declarations,
    is_safe_to_convert,
    is_safe_to_localize,
)


def _parse(source: str) -> ast.Module:
    return ast.parse(textwrap.dedent(source))


class TestIsSafeToConvert:
    """is_safe_to_convert: None when safe, the specific UnsafeReason otherwise."""

    def test_returns_none_when_safe(self) -> None:
        """A TypeVar used only inside functions, not exported, is safe to convert."""
        tree = _parse("""
            from typing import TypeVar

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)
        decl_stmt = find_type_param_declarations(tree)["T"]

        assert_that(is_safe_to_convert(tree, "T", decl_stmt), is_(None))

    @pytest.mark.parametrize(
        ("source", "expected_reason"),
        [
            (
                """
                from typing import TypeVar

                __all__ = ["T"]

                def a(x: T) -> T:
                    return x

                T = TypeVar("T")
                """,
                UnsafeReason.DECLARED_TYPEVAR_EXPORTED,
            ),
            (
                """
                from typing import TypeVar, Generic

                def a(x: T) -> T:
                    return x

                class Box(Generic[T]):
                    pass

                T = TypeVar("T")
                """,
                UnsafeReason.USED_OUTSIDE_FUNCTION,
            ),
        ],
    )
    def test_returns_the_specific_reason_when_unsafe(self, source: str, expected_reason: UnsafeReason) -> None:
        """Each unsafe condition is distinguishable, not collapsed into one generic reason."""
        tree = _parse(source)
        decl_stmt = find_type_param_declarations(tree)["T"]

        assert_that(is_safe_to_convert(tree, "T", decl_stmt), is_(expected_reason))


class TestIsSafeToLocalize:
    """is_safe_to_localize: None when safe, the specific UnsafeReason otherwise."""

    def test_returns_none_when_safe(self) -> None:
        """A TypeVar not exported and not used in a Generic[...] base is safe to localize."""
        tree = _parse("""
            from typing import TypeVar

            T = TypeVar("T")

            def a(x: T) -> T:
                return x
        """)

        assert_that(is_safe_to_localize(tree, "T"), is_(None))

    @pytest.mark.parametrize(
        ("source", "expected_reason"),
        [
            (
                """
                from typing import TypeVar

                __all__ = ["T"]

                T = TypeVar("T")
                """,
                UnsafeReason.ORIGIN_MODULE_EXPORTS_NAME,
            ),
            (
                """
                from typing import TypeVar, Generic

                T = TypeVar("T")

                class Box(Generic[T]):
                    pass
                """,
                UnsafeReason.USED_IN_EXPORTED_GENERIC_BASE,
            ),
        ],
    )
    def test_returns_the_specific_reason_when_unsafe(self, source: str, expected_reason: UnsafeReason) -> None:
        """Each unsafe condition is distinguishable, not collapsed into one generic reason."""
        tree = _parse(source)

        assert_that(is_safe_to_localize(tree, "T"), is_(expected_reason))

"""Tests for type_var_domain's safety predicates and their UnsafeReason results."""

import ast
import textwrap

import pytest
from hamcrest import assert_that, is_

from renaissance.recipes.type_var_domain import (
    UnsafeReason,
    is_safe_to_convert,
    is_safe_to_localize,
)


def _parse(source: str) -> ast.Module:
    return ast.parse(textwrap.dedent(source))


class TestIsSafeToConvert:
    """is_safe_to_convert: None when safe, the specific UnsafeReason otherwise."""

    def test_returns_none_when_safe(self) -> None:
        """A TypeVar not exported and not imported by another project file is safe to convert, whatever else is."""
        tree = _parse("""
            from typing import TypeVar

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)

        assert_that(is_safe_to_convert(tree, "T", frozenset({"U"})), is_(None))

    @pytest.mark.parametrize(
        ("dunder_all", "imported_elsewhere", "expected_reason"),
        [
            pytest.param('__all__ = ["T"]', frozenset(), UnsafeReason.DECLARED_TYPEVAR_EXPORTED, id="exported-via-dunder-all"),
            pytest.param("", frozenset({"T"}), UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT, id="imported-elsewhere"),
        ],
    )
    def test_returns_the_specific_reason_when_unsafe(
        self, dunder_all: str, imported_elsewhere: frozenset[str], expected_reason: UnsafeReason
    ) -> None:
        """Each unsafe condition is distinguishable, not collapsed into one generic reason."""
        tree = _parse(f"""
            from typing import TypeVar

            {dunder_all}

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)

        assert_that(is_safe_to_convert(tree, "T", imported_elsewhere), is_(expected_reason))


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

    def test_ignores_non_generic_subscripted_base_and_plain_base(self) -> None:
        """AI: Verify a TypeVar used only as a subscript of a non-Generic base stays safe to localize."""
        tree = _parse("""
            from typing import TypeVar
            from collections.abc import Mapping

            T = TypeVar("T")

            class Plain(object):
                pass

            class Box(Mapping[T]):
                pass
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
            (
                """
                import sys

                if sys.version_info >= (3, 13):
                    from typing import TypeVar
                else:
                    from typing_extensions import TypeVar

                T = TypeVar("T", default=None)
                """,
                UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY,
            ),
            (
                """
                try:
                    from typing import ParamSpec
                except ImportError:
                    from typing_extensions import ParamSpec

                T = ParamSpec("T")
                """,
                UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY,
            ),
        ],
    )
    def test_returns_the_specific_reason_when_unsafe(self, source: str, expected_reason: UnsafeReason) -> None:
        """Each unsafe condition is distinguishable, not collapsed into one generic reason."""
        tree = _parse(source)

        assert_that(is_safe_to_localize(tree, "T"), is_(expected_reason))

    def test_ignores_conditional_imports_of_other_names(self) -> None:
        """A conditional import of an unrelated name doesn't make an unconditionally imported constructor unsafe."""
        tree = _parse("""
            from typing import TYPE_CHECKING, TypeVar

            if TYPE_CHECKING:
                from collections.abc import Sequence

            T = TypeVar("T")
        """)

        assert_that(is_safe_to_localize(tree, "T"), is_(None))

"""Tests for type_var_domain's safety predicates and their UnsafeReason results."""

import ast
import re
import textwrap
from pathlib import Path

import pytest
from hamcrest import assert_that, is_

from renaissance.recipes.type_var_domain import (
    UNSAFE_RULES,
    UnsafeReason,
    is_safe_to_localize,
    is_safe_to_remove,
)


def _parse(source: str) -> ast.Module:
    return ast.parse(textwrap.dedent(source))


class TestIsSafeToRemove:
    """is_safe_to_remove: None when safe, the specific UnsafeReason otherwise."""

    def test_returns_none_when_safe(self) -> None:
        """A TypeVar not exported and not imported by another project file is safe to convert, whatever else is."""
        tree = _parse("""
            from typing import TypeVar

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)

        assert_that(is_safe_to_remove(tree, "T", frozenset({"U"})), is_(None))

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

        assert_that(is_safe_to_remove(tree, "T", imported_elsewhere), is_(expected_reason))


class TestIsSafeToLocalize:
    """is_safe_to_localize: None when safe, the specific UnsafeReason otherwise."""

    def test_returns_none_when_safe(self) -> None:
        """A TypeVar is safe to localize, even when its origin exports it, unless its constructor is imported conditionally."""
        tree = _parse("""
            from typing import TypeVar

            __all__ = ["T"]

            T = TypeVar("T")

            def a(x: T) -> T:
                return x
        """)

        assert_that(is_safe_to_localize(tree, "T"), is_(None))

    @pytest.mark.parametrize(
        "class_header",
        [
            pytest.param("class Plain(object):", id="plain-class"),
            pytest.param("class Box(Generic[T]):", id="generic"),
            pytest.param("class Box(typing.Generic[T]):", id="qualified-generic"),
            pytest.param("class Box(Protocol[T]):", id="protocol"),
            pytest.param("class Box(Mapping[T]):", id="generic-abc"),
            pytest.param("class Box(Base[int, T]):", id="generic-subclass"),
            pytest.param("class Box[T]:", id="pep695-class"),
        ],
    )
    def test_class_at_the_origin_does_not_block_localizing(self, class_header: str) -> None:
        """A class at the origin, generic over T or not, keeps its own T, so copying T elsewhere is safe."""
        tree = _parse(f"""
            import typing
            from collections.abc import Mapping
            from typing import Generic, Protocol, TypeVar

            T = TypeVar("T")

            {class_header}
                pass
        """)

        assert_that(is_safe_to_localize(tree, "T"), is_(None))

    @pytest.mark.parametrize(
        ("source", "expected_reason"),
        [
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


_FEATURE_DOC = Path(__file__).resolve().parents[2] / "docs" / "user" / "features" / "typevar-modernization.md"


class TestUnsafeRuleDocAnchors:
    """Every UnsafeRule's documentation anchor exists where the CLI's report links to it."""

    @pytest.mark.parametrize("reason", list(UnsafeReason))
    def test_anchor_is_set_on_a_heading(self, reason: UnsafeReason) -> None:
        """The rule's anchor is attached to a heading line, the only place attr_list turns it into a link target."""
        anchor = UNSAFE_RULES[reason].doc_anchor
        heading = re.compile(rf"^#+ .+ \{{ #{re.escape(anchor)} \}}$", re.MULTILINE)

        assert_that(bool(heading.search(_FEATURE_DOC.read_text(encoding="utf-8"))), is_(True))

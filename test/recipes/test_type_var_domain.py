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
    """Parse source after removing its common indentation."""
    return ast.parse(textwrap.dedent(source))


class TestIsSafeToRemove:
    """is_safe_to_remove: None when safe, the specific UnsafeReason otherwise."""

    def test_returns_none_when_safe(self) -> None:
        """A TypeVar not exported and not imported by another project file is safe to remove, whatever else is."""
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

    @pytest.mark.parametrize(
        "dunder_all",
        [
            pytest.param('__all__: list[str] = ["T"]', id="annotated"),
            pytest.param('__all__ = []\n__all__ += ["T"]', id="augmented"),
            pytest.param('__all__ = []\n__all__.extend(["T"])', id="extend"),
            pytest.param('__all__ = []\n__all__.append("T")', id="append"),
        ],
    )
    @pytest.mark.xfail(reason="_find_dunder_all only reads a plain `__all__ = [...]` assignment.", strict=True)
    def test_exported_name_is_unsafe_whatever_form_dunder_all_takes(self, dunder_all: str) -> None:
        """A TypeVar exported through any common form of `__all__` is reported as exported."""
        tree = _parse(f'from typing import TypeVar\n{dunder_all}\nT = TypeVar("T")\n')

        assert_that(is_safe_to_remove(tree, "T"), is_(UnsafeReason.DECLARED_TYPEVAR_EXPORTED))


class TestIsSafeToLocalize:
    """is_safe_to_localize: None when safe, the specific UnsafeReason otherwise."""

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param('from typing import TypeVar\nT = TypeVar("T")\n', id="unconditional-import"),
            pytest.param(
                "from typing import TYPE_CHECKING, TypeVar\n"
                "if TYPE_CHECKING:\n"
                "    from collections.abc import Sequence\n"
                'T = TypeVar("T")\n',
                id="conditional-import-of-another-name",
            ),
        ],
    )
    def test_returns_none_when_safe(self, source: str) -> None:
        """A TypeVar whose constructor its origin imports unconditionally is safe to localize, whatever else is conditional."""
        assert_that(is_safe_to_localize(_parse(source), "T"), is_(None))

    @pytest.mark.parametrize(
        ("source", "expected_reason"),
        [
            pytest.param(
                """
                import sys

                if sys.version_info >= (3, 13):
                    from typing import TypeVar
                else:
                    from typing_extensions import TypeVar

                T = TypeVar("T", default=None)
                """,
                UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY,
                id="if-version-check",
            ),
            pytest.param(
                """
                try:
                    from typing import ParamSpec
                except ImportError:
                    from typing_extensions import ParamSpec

                T = ParamSpec("T")
                """,
                UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY,
                id="try-except-import",
            ),
        ],
    )
    def test_returns_the_specific_reason_when_unsafe(self, source: str, expected_reason: UnsafeReason) -> None:
        """Each unsafe condition is distinguishable, not collapsed into one generic reason."""
        tree = _parse(source)

        assert_that(is_safe_to_localize(tree, "T"), is_(expected_reason))


_FEATURE_DOC = Path(__file__).resolve().parents[2] / "docs" / "user" / "features" / "typevar-modernization.md"


class TestUnsafeRuleDocAnchors:
    """Every UnsafeRule's documentation anchor exists where the CLI's report links to it."""

    @pytest.mark.parametrize("reason", list(UnsafeReason))
    def test_anchor_is_set_on_a_heading(self, reason: UnsafeReason) -> None:
        """The rule's anchor is attached to a heading line, the only place attr_list turns it into a link target."""
        anchor = UNSAFE_RULES[reason].doc_anchor
        heading = re.compile(rf"^#+ .+ \{{ #{re.escape(anchor)} \}}$", re.MULTILINE)

        assert_that(bool(heading.search(_FEATURE_DOC.read_text(encoding="utf-8"))), is_(True))

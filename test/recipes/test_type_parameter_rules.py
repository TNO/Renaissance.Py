# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for type_parameter_rules's safety predicates and their UnsafeReason results."""

import re
import textwrap
from collections import Counter
from pathlib import Path
from typing import cast

import libcst as cst
import pytest
from hamcrest import assert_that, equal_to, not_

from renaissance.recipes.type_parameter_rules import (
    CONVERSION_RULES,
    LOCALIZATION_RULES,
    PEP_696_MINIMUM,
    REMOVAL_RULES,
    UNSAFE_RULES,
    UnsafeReason,
    conversion_refusal,
    is_safe_to_localize,
    is_safe_to_remove,
)


def _parse(source: str) -> cst.Module:
    """Parse source after removing its common indentation."""
    return cst.parse_module(textwrap.dedent(source))


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

        assert_that(is_safe_to_remove(tree, "T", frozenset({"U"})), equal_to(None))

    @pytest.mark.parametrize(
        ("dunder_all", "imported_elsewhere", "expected_reason"),
        [
            pytest.param('__all__ = ["T"]', frozenset[str](), UnsafeReason.DECLARED_TYPEVAR_EXPORTED, id="exported-via-dunder-all"),
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

        assert_that(is_safe_to_remove(tree, "T", imported_elsewhere), equal_to(expected_reason))


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
        assert_that(is_safe_to_localize(_parse(source), "T"), equal_to(None))

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

        assert_that(is_safe_to_localize(tree, "T"), equal_to(expected_reason))


_FEATURE_DOC = Path(__file__).resolve().parents[2] / "docs" / "user" / "features" / "type-parameter-modernization.md"


class TestUnsafeRuleDocAnchors:
    """Every UnsafeRule's documentation anchor exists where the CLI's report links to it."""

    @pytest.mark.parametrize("reason", list(UnsafeReason))
    def test_anchor_is_set_on_a_heading(self, reason: UnsafeReason) -> None:
        """The rule's anchor is attached to a heading line, the only place attr_list turns it into a link target."""
        anchor = UNSAFE_RULES[reason].doc_anchor
        heading = re.compile(rf"^#+ .+ \{{ #{re.escape(anchor)} \}}$", re.MULTILINE)

        assert_that(heading.search(_FEATURE_DOC.read_text(encoding="utf-8")), not_(None))


class TestConversionRefusal:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("declaration", "min_python", "expected"),
        [
            pytest.param('T = TypeVar("T")', (3, 12), None, id="plain-declaration"),
            pytest.param('T = TypeVar("T", default=int)', (3, 12), UnsafeReason.PEP696_VERSION_GATE, id="default-below-3.13"),
            pytest.param('T = TypeVar("T", default=int)', PEP_696_MINIMUM, None, id="default-from-3.13"),
            pytest.param('P = ParamSpec("P", bound=int)', (3, 12), UnsafeReason.NO_PEP695_EQUIVALENT, id="bound-on-a-param-spec"),
            pytest.param(
                'T = TypeVar("T", default=int, **options)',
                (3, 12),
                UnsafeReason.NO_PEP695_EQUIVALENT,
                id="the-first-registered-rule-wins",
            ),
        ],
    )
    def test_returns_none_when_convertible_else_the_first_reason(
        self,
        declaration: str,
        min_python: tuple[int, int],
        expected: UnsafeReason | None,
    ) -> None:
        """Verify a declaration is refused only for a reason that applies to it, and the first registered reason wins."""
        statement = cast("cst.SimpleStatementLine", cst.parse_statement(declaration))

        assert_that(conversion_refusal(cast("cst.Assign", statement.body[0]), min_python), equal_to(expected))


class TestRefusalRuleRegistry:
    """See module docstring."""

    def test_no_reason_is_registered_twice(self) -> None:
        """Verify each UnsafeReason is enforced by at most one rule, so a report never has two rules for one reason."""
        registered = [rule.reason for rules in (CONVERSION_RULES, REMOVAL_RULES, LOCALIZATION_RULES) for rule in rules]

        assert_that(max(Counter(registered).values()), equal_to(1))

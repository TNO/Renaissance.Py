# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for TypeParameterCheck.remove_orphaned_declarations."""

import textwrap
from collections.abc import Callable

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entry, not_

from renaissance.recipes.type_parameter_check import TypeParameterCheck
from renaissance.recipes.type_parameter_rules import UnsafeReason

ALREADY_CONVERTED_SOURCE = """
from typing import TypeVar
T = TypeVar('T')

def b[T](x: T) -> T:
    return x
"""

UNREFERENCED_SOURCE = """
from typing import TypeVar
T = TypeVar('T')

def b() -> None:
    pass
"""

NESTED_ONLY_CONVERTED_SOURCE = """
from typing import TypeVar
T = TypeVar('T')

def outer() -> None:
    def inner[T](x: T) -> T:
        return x
"""

CLOSURE_IN_CONVERTED_FUNCTION_SOURCE = """
from typing import TypeVar
T = TypeVar('T')

def outer[T](x: T) -> T:
    def inner(y: T) -> T:
        return y
    return inner(x)
"""

CLASS_WITH_OWN_TYPE_PARAMETER_SOURCE = """
from typing import TypeVar
T = TypeVar('T')

class Box[T]:
    def get(self, x: T) -> T:
        return x
"""


class TestTypeParameterCheckOrphaned:
    """See module docstring."""

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(ALREADY_CONVERTED_SOURCE, id="already-converted"),
            pytest.param(UNREFERENCED_SOURCE, id="unreferenced"),
            pytest.param(NESTED_ONLY_CONVERTED_SOURCE, id="only-nested-function-converted"),
            pytest.param(CLOSURE_IN_CONVERTED_FUNCTION_SOURCE, id="closure-inside-converted-function"),
            pytest.param(CLASS_WITH_OWN_TYPE_PARAMETER_SOURCE, id="class-with-own-type-parameter"),
        ],
    )
    def test_removes_declaration_whose_references_are_all_shadowed(
        self,
        create_type_parameter_check: Callable[[str], TypeParameterCheck],
        source: str,
    ) -> None:
        """Verify a declaration whose references are all shadowed by PEP 695 parameters, or absent, is removed."""
        subject = create_type_parameter_check(source)

        result = subject.remove_orphaned_declarations()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, not_(contains_string("T = TypeVar")))
        for def_line in (line.strip() for line in textwrap.dedent(source).splitlines() if line.strip().startswith("def ")):
            assert_that(output, contains_string(def_line))

    @pytest.mark.parametrize(
        "declaration",
        [
            pytest.param("T = TypeVar('T')  # noqa: PLC0105", id="trailing-comment"),
            pytest.param("T = TypeVar(\n    'T',\n    bound=int,\n)  # noqa: PLC0105", id="multi-line-trailing-comment"),
        ],
    )
    def test_removing_a_declaration_removes_the_comment_trailing_it(
        self,
        create_type_parameter_check: Callable[[str], TypeParameterCheck],
        declaration: str,
    ) -> None:
        """Verify the comment trailing a removed declaration goes with it instead of staying behind on a line of its own."""
        subject = create_type_parameter_check(f"from typing import TypeVar\n{declaration}\n\ndef b() -> None:\n    pass\n")

        result = subject.remove_orphaned_declarations()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, not_(contains_string("noqa")))

    def test_keeps_declaration_still_used_without_pep695(self, create_type_parameter_check: Callable[[str], TypeParameterCheck]) -> None:
        """Verify a declaration still used by a function without its own type parameter is left alone, unreported."""
        subject = create_type_parameter_check("""
            from typing import TypeVar
            T = TypeVar('T')

            def a[T](x: T) -> T:
                return x
            def b(y: T) -> T:
                return y
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, equal_to({}))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

    @pytest.mark.parametrize(
        "annotation",
        [
            pytest.param('"T"', id="whole-annotation"),
            pytest.param('"list[T]"', id="inside-annotation"),
        ],
    )
    def test_keeps_declaration_used_in_a_string_annotation(
        self, create_type_parameter_check: Callable[[str], TypeParameterCheck], annotation: str
    ) -> None:
        """Verify a declaration referenced only from a string annotation is not removed as orphaned."""
        subject = create_type_parameter_check(f"""
            from typing import TypeVar
            T = TypeVar('T')

            def b(x: {annotation}) -> None:
                pass
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, equal_to({}))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

    def test_keeps_orphaned_declaration_imported_elsewhere(
        self, create_type_parameter_check: Callable[[str], TypeParameterCheck]
    ) -> None:
        """Verify an orphaned declaration is kept and reported unsafe when removing it would break an importer."""
        subject = create_type_parameter_check(ALREADY_CONVERTED_SOURCE)
        subject.project_wide_imported_names = frozenset({"T"})

        result = subject.remove_orphaned_declarations()

        assert_that(result, equal_to({"T": "unsafe"}))
        assert_that(subject.orphaned_unsafe_reasons, equal_to({"T": UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT}))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

    def test_removing_orphaned_declaration_keeps_comment_shared_with_next_declaration(
        self, create_type_parameter_check: Callable[[str], TypeParameterCheck]
    ) -> None:
        """Verify removing an orphaned declaration keeps a leading comment that also documents the next declaration."""
        subject = create_type_parameter_check("""
            from typing import TypeVar

            # explains both T and U below
            T = TypeVar('T')
            U = TypeVar('U')

            Pair = tuple[U, U]

            def b[T](x: T) -> T:
                return x
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("# explains both T and U below"))
        assert_that(output, contains_string("U = TypeVar('U')"))

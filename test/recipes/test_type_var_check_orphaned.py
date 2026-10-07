"""Tests for TypeVarCheck.remove_orphaned_declarations."""

import textwrap
from collections.abc import Callable
from typing import cast

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entry, not_

from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.type_var_check import TypeVarCheck
from renaissance.recipes.type_var_domain import UnsafeReason

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


class TestTypeVarCheckOrphaned:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("source", "min_python"),
        [
            pytest.param(ALREADY_CONVERTED_SOURCE, (3, 12), id="already-converted"),
            pytest.param(ALREADY_CONVERTED_SOURCE, (3, 11), id="already-converted-below-pep695"),
            pytest.param(UNREFERENCED_SOURCE, (3, 11), id="unreferenced-below-pep695"),
            pytest.param(NESTED_ONLY_CONVERTED_SOURCE, (3, 12), id="only-nested-function-converted"),
            pytest.param(CLOSURE_IN_CONVERTED_FUNCTION_SOURCE, (3, 12), id="closure-inside-converted-function"),
        ],
    )
    def test_removes_declaration_whose_references_are_all_shadowed(
        self,
        make_recipe: Callable[[type[PythonRefactoring], str], PythonRefactoring],
        source: str,
        min_python: tuple[int, int],
    ) -> None:
        """Verify a declaration whose references are all shadowed by PEP 695 parameters, or absent, is removed."""
        subject = cast("TypeVarCheck", make_recipe(TypeVarCheck, source))
        subject.min_python = min_python

        result = subject.remove_orphaned_declarations()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, not_(contains_string("T = TypeVar")))
        for def_line in (line.strip() for line in textwrap.dedent(source).splitlines() if line.strip().startswith("def ")):
            assert_that(output, contains_string(def_line))

    def test_keeps_declaration_still_used_without_pep695(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """Verify a declaration still used by a function without its own type parameter is left alone, unreported."""
        subject = create_type_var_check("""
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
        ("imported_elsewhere", "expected_reason"),
        [
            pytest.param(frozenset(), UnsafeReason.DECLARED_TYPEVAR_EXPORTED, id="exported-via-dunder-all"),
            pytest.param(frozenset({"T"}), UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT, id="imported-elsewhere"),
        ],
    )
    def test_keeps_orphaned_declaration_that_is_unsafe_to_remove(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        imported_elsewhere: frozenset[str],
        expected_reason: UnsafeReason,
    ) -> None:
        """Verify an orphaned declaration is kept and reported unsafe when removing it would break an importer."""
        source = ALREADY_CONVERTED_SOURCE if imported_elsewhere else '__all__ = ["T"]\n' + ALREADY_CONVERTED_SOURCE
        subject = create_type_var_check(source)
        subject.project_wide_imported_names = imported_elsewhere

        result = subject.remove_orphaned_declarations()

        assert_that(result, equal_to({"T": "unsafe"}))
        assert_that(subject.orphaned_unsafe_reasons, equal_to({"T": expected_reason}))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

    def test_removing_orphaned_declaration_keeps_comment_shared_with_next_declaration(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
        """Verify removing an orphaned declaration keeps a leading comment that also documents the next declaration."""
        subject = create_type_var_check("""
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

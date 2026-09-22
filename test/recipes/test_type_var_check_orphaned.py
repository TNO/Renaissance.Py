"""Tests for TypeVarCheck.remove_orphaned_declarations."""

from collections.abc import Callable

from hamcrest import assert_that, contains_string, has_entry, has_key, is_not, not_

from renaissance.recipes.type_var_check import TypeVarCheck
from renaissance.recipes.type_var_domain import UnsafeReason


class TestTypeVarCheckOrphaned:
    """See module docstring."""

    def test_removes_orphaned_declaration_after_manual_or_ruff_pep695_conversion(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
        """AI: Verify a TypeVar declaration left orphaned by a manual/ruff PEP 695 conversion is removed."""
        subject = create_type_var_check("""
            from typing import TypeVar
            T = TypeVar('T')

            def b[T](x: T) -> T:
                return x
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))
        assert_that(output, not_(contains_string("T = TypeVar")))
        assert_that(output, contains_string("from typing import TypeVar"))

    def test_removes_fully_unused_declaration(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVar declaration with no references anywhere is removed."""
        subject = create_type_var_check("""
            from typing import TypeVar
            T = TypeVar('T')

            def b() -> None:
                pass
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, not_(contains_string("T = TypeVar")))
        assert_that(output, contains_string("from typing import TypeVar"))

    def test_does_not_touch_declaration_still_live_outside_shadow(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVar declaration still live in an un-shadowed function is left untouched, unflagged."""
        subject = create_type_var_check("""
            from typing import TypeVar
            T = TypeVar('T')

            def a[T](x: T) -> T:
                return x
            def b(y: T) -> T:
                return y
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, is_not(has_key("T")))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

    def test_does_not_remove_declaration_used_in_generic_base(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVar declaration also used in a Generic[...] base is left untouched, unflagged."""
        # The Generic[T] base is a real, non-shadowed use, so this is never even flagged -
        # same as any other still-live declaration.
        subject = create_type_var_check("""
            from typing import TypeVar, Generic
            T = TypeVar('T')

            class Box(Generic[T]):
                pass

            def b[T](x: T) -> T:
                return x
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, is_not(has_key("T")))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

    def test_removing_orphaned_declaration_keeps_comment_shared_with_next_declaration(
        self, create_type_var_check: Callable[[str], TypeVarCheck],
    ) -> None:
        # T's leading comment also documents U, declared right after it with no comment of its
        # own - it must not be treated as belonging solely to the removed T declaration.
        subject = create_type_var_check("""
            from typing import TypeVar

            # explains both T and U below
            T = TypeVar('T')
            U = TypeVar('U')

            def b[T](x: T, y: U) -> T:
                return x
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("# explains both T and U below"))
        assert_that(output, contains_string("U = TypeVar('U')"))

    def test_does_not_remove_orphaned_declaration_imported_elsewhere_in_project(
        self, create_type_var_check: Callable[[str], TypeVarCheck],
    ) -> None:
        # T is shadowed here (orphaned locally), but another project file imports it directly
        # from this module - removing it would break that import, __all__ or not.
        subject = create_type_var_check("""
            from typing import TypeVar
            T = TypeVar('T')

            def b[T](x: T) -> T:
                return x
        """)
        subject.project_wide_imported_names = frozenset({"T"})
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.orphaned_unsafe_reasons, has_entry("T", UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

    def test_does_not_remove_orphaned_declaration_in_dunder_all(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify an orphaned but __all__-exported TypeVar declaration is reported unsafe, not removed."""
        # Every reference is shadowed, but T is still exported public API via __all__, so
        # removing the declaration would break importers - flagged "unsafe", not silently fixed.
        subject = create_type_var_check("""
            from typing import TypeVar

            __all__ = ["T"]

            T = TypeVar('T')

            def b[T](x: T) -> T:
                return x
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.orphaned_unsafe_reasons, has_entry("T", UnsafeReason.DECLARED_TYPEVAR_EXPORTED))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

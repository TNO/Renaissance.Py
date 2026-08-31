"""Tests for TypeVarCheck.remove_orphaned_declarations."""

from collections.abc import Callable

from hamcrest import assert_that, contains_string, has_entry, has_key, is_not, not_

from renaissance.refactoring.type_var_check import TypeVarCheck


class TestTypeVarCheckOrphaned:
    """See module docstring."""

    def test_removes_orphaned_declaration_after_manual_or_ruff_pep695_conversion(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
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
        assert_that(output, not_(contains_string("TypeVar")))

    def test_removes_fully_unused_declaration(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        subject = create_type_var_check("""
            from typing import TypeVar
            T = TypeVar('T')

            def b() -> None:
                pass
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), not_(contains_string("TypeVar")))

    def test_does_not_touch_declaration_still_live_outside_shadow(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
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

    def test_does_not_remove_orphaned_declaration_in_dunder_all(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
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
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

"""Tests for TypeVarTupleCheck.fix_legacy_unpack_usage."""

import textwrap
from collections.abc import Callable  # noqa: TC003
from pathlib import Path  # noqa: TC003

from hamcrest import assert_that, contains_string, equal_to, has_entry, is_not

from renaissance.recipes.python_refactoring import PythonRefactoring  # noqa: TC001
from renaissance.recipes.type_var_tuple_check import PEP_646_MINIMUM, TypeVarTupleCheck


class TestFixLegacyUnpackUsage:
    """See module docstring."""

    def test_rewrites_generic_base_unpack_to_star_syntax(
        self, create_type_var_tuple_check: Callable[[str], TypeVarTupleCheck],
    ) -> None:
        subject = create_type_var_tuple_check("""
            from typing import TypeVarTuple, Generic, Unpack
            Ts = TypeVarTuple("Ts")
            class Foo(Generic[Unpack[Ts]]):
                pass
        """)
        result = subject.fix_legacy_unpack_usage()

        assert_that(result, has_entry("Ts", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("class Foo(Generic[*Ts]):"))
        assert_that(output, is_not(contains_string("Unpack")))

    def test_rewrites_function_signature_unpack_to_star_syntax(
        self, create_type_var_tuple_check: Callable[[str], TypeVarTupleCheck],
    ) -> None:
        subject = create_type_var_tuple_check("""
            from typing import TypeVarTuple, Unpack
            Ts = TypeVarTuple("Ts")
            def foo(*args: Unpack[Ts]) -> None:
                pass
        """)
        result = subject.fix_legacy_unpack_usage()

        assert_that(result, has_entry("Ts", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def foo(*args: *Ts) -> None:"))
        assert_that(output, is_not(contains_string("Unpack")))

    def test_rewrites_every_occurrence_of_the_same_name(
        self, create_type_var_tuple_check: Callable[[str], TypeVarTupleCheck],
    ) -> None:
        subject = create_type_var_tuple_check("""
            from typing import TypeVarTuple, Unpack
            Ts = TypeVarTuple("Ts")
            def foo(*args: Unpack[Ts]) -> tuple[Unpack[Ts]]:
                return args
        """)
        result = subject.fix_legacy_unpack_usage()

        assert_that(result, has_entry("Ts", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def foo(*args: *Ts) -> tuple[*Ts]:"))
        assert_that(output, is_not(contains_string("Unpack")))

    def test_no_legacy_usage_returns_empty(self, create_type_var_tuple_check: Callable[[str], TypeVarTupleCheck]) -> None:
        subject = create_type_var_tuple_check("""
            from typing import TypeVarTuple
            Ts = TypeVarTuple("Ts")
            def foo(*args: *Ts) -> None:
                pass
        """)
        result = subject.fix_legacy_unpack_usage()

        assert_that(result, equal_to({}))

    def test_version_gate_below_minimum_reports_unsafe_and_leaves_file_untouched(
        self, make_recipe: Callable[[type[PythonRefactoring], str], PythonRefactoring],
    ) -> None:
        code = """
            from typing import TypeVarTuple, Unpack
            Ts = TypeVarTuple("Ts")
            def foo(*args: Unpack[Ts]) -> None:
                pass
        """
        subject = make_recipe(TypeVarTupleCheck, code)
        subject.min_python_override = (3, 10)

        result = subject.fix_legacy_unpack_usage()

        assert_that(result, has_entry("Ts", "unsafe"))
        assert_that(subject.apply_to_string(), contains_string("Unpack[Ts]"))

    def test_unpack_import_kept_when_still_used_for_unrelated_typed_dict_kwargs(
        self, create_type_var_tuple_check: Callable[[str], TypeVarTupleCheck],
    ) -> None:
        subject = create_type_var_tuple_check("""
            from typing import TypeVarTuple, Unpack
            from mymodule import Kwargs
            Ts = TypeVarTuple("Ts")
            def foo(*args: Unpack[Ts], **kwargs: Unpack[Kwargs]) -> None:
                pass
        """)
        result = subject.fix_legacy_unpack_usage()

        assert_that(result, has_entry("Ts", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("*args: *Ts"))
        assert_that(output, contains_string("from typing import TypeVarTuple, Unpack"))
        assert_that(output, contains_string("**kwargs: Unpack[Kwargs]"))

    def test_fix_is_written_to_a_real_file_not_just_queued_in_memory(self, tmp_path: Path) -> None:
        """Regression test: fix_legacy_unpack_usage() must commit(), not just queue the rewrite."""
        target = tmp_path / "mod.py"
        target.write_text(
            textwrap.dedent("""\
                from typing import TypeVarTuple, Unpack

                Ts = TypeVarTuple("Ts")


                def foo(*args: Unpack[Ts]) -> None:
                    pass
                """),
            encoding="utf-8",
        )
        subject = TypeVarTupleCheck(target)
        subject.min_python_override = PEP_646_MINIMUM

        result = subject.fix_legacy_unpack_usage()

        assert_that(result, has_entry("Ts", "fixed"))
        written = target.read_text(encoding="utf-8")
        assert_that(written, contains_string("def foo(*args: *Ts) -> None:"))
        assert_that(written, is_not(contains_string("Unpack")))

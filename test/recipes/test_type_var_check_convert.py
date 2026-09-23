"""Tests for TypeVarCheck.convert_declared_typevars."""

import ast
from collections.abc import Callable
from typing import cast

from hamcrest import assert_that, contains_string, has_entry, not_

from renaissance.recipes.python_refactoring import PythonRefactoring  # noqa: TC001
from renaissance.recipes.type_var_check import TypeVarCheck
from renaissance.recipes.type_var_domain import UnsafeReason


class TestTypeVarCheckConvert:
    """See module docstring."""

    def test_converts_typevar_shared_across_functions_to_pep695(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVar shared across two functions converts both to PEP 695 syntax."""
        subject = create_type_var_check("""
            from typing import TypeVar

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def a[T](x: T) -> T:"))
        assert_that(output, contains_string("def b[T](y: T) -> T:"))
        assert_that(output, not_(contains_string("T = TypeVar")))
        assert_that(output, contains_string("from typing import TypeVar"))

    def test_converts_typevar_shared_across_methods_to_pep695(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVar shared across two methods of the same class converts both to PEP 695 syntax."""
        subject = create_type_var_check("""
            from typing import TypeVar

            class Foo:
                def a(self, x: T) -> T:
                    return x
                def b(self, y: T) -> T:
                    return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def a[T](self, x: T) -> T:"))
        assert_that(output, contains_string("def b[T](self, y: T) -> T:"))

    def test_converts_function_with_multiline_docstring_without_double_indenting(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
        """AI: Verify converting a signature doesn't double-indent its function's multi-line docstring."""
        # A multi-line docstring's continuation lines must not get double-indented.
        subject = create_type_var_check("""
            from typing import TypeVar

            class Foo:
                def cast(self, x: T) -> T:
                    \"\"\"First line.

                    Second line already indented.
                    Third line too.
                    \"\"\"
                    return x
                def other(self, y: T) -> T:
                    return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def cast[T](self, x: T) -> T:"))
        assert_that(output, contains_string('        """First line.'))
        assert_that(output, contains_string("        Second line already indented."))
        assert_that(output, contains_string("        Third line too."))
        assert_that(output, contains_string('        """\n        return x'))
        # would appear if the continuation lines got shifted twice
        assert_that(output, not_(contains_string("            Second line already indented.")))

    def test_converts_function_with_nested_docstring_indentation(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify converting a signature preserves a docstring's internal nested block's relative indentation."""
        # A docstring with an internal nested block (e.g. Sphinx's ".. seealso::") must keep
        # that block's *relative* extra indentation, not get flattened to one uniform level.
        subject = create_type_var_check("""
            from typing import TypeVar

            class Foo:
                def cast(self, x: T) -> T:
                    \"\"\"Produce a cast.

                    .. seealso::

                        :ref:`tutorial_casts`
                    \"\"\"
                    return x
                def other(self, y: T) -> T:
                    return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("        .. seealso::"))
        assert_that(output, contains_string("            :ref:`tutorial_casts`"))

    def test_converts_function_with_single_line_docstring(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify converting a signature leaves a single-line docstring untouched."""
        subject = create_type_var_check("""
            from typing import TypeVar

            class Foo:
                def cast(self, x: T) -> T:
                    \"\"\"One liner.\"\"\"
                    return x
                def other(self, y: T) -> T:
                    return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def cast[T](self, x: T) -> T:"))
        assert_that(output, contains_string('        """One liner."""'))

    def test_converts_bound_typevar(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a bound TypeVar converts to a PEP 695 type param carrying the same bound."""
        subject = create_type_var_check("""
            from typing import TypeVar

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            T = TypeVar("T", bound=int)
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("def a[T: int](x: T) -> T:"))

    def test_converts_constrained_typevar(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a constrained TypeVar converts to a PEP 695 type param carrying the same constraints."""
        subject = create_type_var_check("""
            from typing import TypeVar

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            T = TypeVar("T", int, str)
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("def a[T: (int, str)](x: T) -> T:"))

    def test_converts_paramspec(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a ParamSpec shared across two functions converts both to PEP 695 `**P` syntax."""
        subject = create_type_var_check("""
            from typing import ParamSpec

            def a(f: Callable[P, int]) -> Callable[P, int]:
                return f
            def b(f: Callable[P, str]) -> Callable[P, str]:
                return f

            P = ParamSpec("P")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("P", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("def a[**P]"))
        assert_that(subject.apply_to_string(), contains_string("def b[**P]"))

    def test_converts_typevartuple(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVarTuple converts to PEP 695 `*Ts` syntax."""
        subject = create_type_var_check("""
            from typing import TypeVarTuple

            def a(*args: *Ts) -> tuple[*Ts]:
                return args
            def b(*args: *Ts) -> tuple[*Ts]:
                return args

            Ts = TypeVarTuple("Ts")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("Ts", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("def a[*Ts]"))

    def test_does_not_convert_typevar_used_in_generic_base(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVar also used in a class's Generic[...] base is left unconverted, marked unsafe."""
        subject = create_type_var_check("""
            from typing import TypeVar, Generic

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            class Box(Generic[T]):
                pass

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.converted_unsafe_reasons, has_entry("T", UnsafeReason.USED_OUTSIDE_FUNCTION))
        assert_that(subject.apply_to_string(), contains_string('T = TypeVar("T")'))

    def test_does_not_convert_typevar_in_dunder_all(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVar exported via __all__ is left unconverted, marked unsafe."""
        subject = create_type_var_check("""
            from typing import TypeVar

            __all__ = ["T"]

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.converted_unsafe_reasons, has_entry("T", UnsafeReason.DECLARED_TYPEVAR_EXPORTED))
        assert_that(subject.apply_to_string(), contains_string('T = TypeVar("T")'))

    def test_does_not_convert_typevar_imported_elsewhere_in_project(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """A TypeVar imported directly by another project file is reported unsafe and not converted, even without __all__."""
        subject = create_type_var_check("""
            from typing import TypeVar

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            T = TypeVar("T")
        """)
        subject.project_wide_imported_names = frozenset({"T"})
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.converted_unsafe_reasons, has_entry("T", UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT))
        assert_that(subject.apply_to_string(), contains_string('T = TypeVar("T")'))

    def test_removes_declaration_but_keeps_import_used_by_other_typevar(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify removing one converted TypeVar's declaration keeps the shared import alive for an unsafe sibling."""
        # T is multi-scope and safe to convert; U is left alone (used in a Generic[...] base),
        # so the shared "from typing import TypeVar" import must survive for U's sake.
        subject = create_type_var_check("""
            from typing import TypeVar, Generic

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            class Box(Generic[U]):
                pass

            T = TypeVar("T")
            U = TypeVar("U")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(result, has_entry("U", "unsafe"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("from typing import TypeVar"))
        assert_that(output, contains_string('U = TypeVar("U")'))
        assert_that(output, not_(contains_string("T = TypeVar")))

    def test_converts_single_scope_typevar_without_ruff(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a TypeVar used by a single function still converts even without a ruff-style leftover."""
        subject = create_type_var_check("""
            from typing import TypeVar

            T = TypeVar('T')

            def b(x: T) -> T:
                return x
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))

    def test_converts_function_preserving_internal_comments(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify converting a signature never touches or drops a comment inside its body."""
        # Converting a function's signature must never touch or drop a comment in its body.
        subject = create_type_var_check("""
            from typing import TypeVar

            def b(x: T) -> T:
                # this explains something non-obvious
                return x

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))
        assert_that(output, contains_string("# this explains something non-obvious"))

    def test_converts_function_preserving_unusual_body_formatting(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify converting a signature never reformats or collapses its body's unusual formatting."""
        # Converting a function's signature must never reformat or collapse its body.
        subject = create_type_var_check("""
            from typing import TypeVar

            def b(x: T) -> T:
                return foo(
                    x,
                    extra=1,
                )

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))
        assert_that(output, contains_string("return foo(\n        x,\n        extra=1,\n    )"))

    def test_does_not_add_redundant_type_param_to_nested_closure(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify a nested closure referencing an enclosing function's converted type param doesn't get its own copy."""
        # A nested closure merely referencing an enclosing function's type param must not get
        # its own shadowing type param - PEP 695 params are already visible in nested scopes.
        subject = create_type_var_check("""
            from typing import ParamSpec
            from collections.abc import Callable

            P = ParamSpec("P")

            def requires(func: Callable[P, int]) -> Callable[P, int]:
                def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:
                    return func(*args, **kwargs)

                return wrapper
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("P", "fixed"))
        output = subject.apply_to_string()
        ast.parse(output)  # raises SyntaxError if the nested closure's edit corrupted the output
        assert_that(output, contains_string("def requires[**P](func: Callable[P, int]) -> Callable[P, int]:"))
        assert_that(output, contains_string("def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:"))
        assert_that(output, not_(contains_string("wrapper[**P]")))

    def test_preserves_multiline_signature_formatting(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify converting a multi-line signature doesn't collapse it onto one line."""
        # Converting a multi-line signature must not collapse it onto one line.
        subject = create_type_var_check("""
            from typing import TypeVar

            def b(
                x: T,
                y: int = 1,
                *,
                z: str | None = None,
            ) -> T:
                return x

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](\n"))
        assert_that(output, contains_string("    x: T,\n"))
        assert_that(output, contains_string("    y: int = 1,\n"))
        assert_that(output, contains_string("    *,\n"))
        assert_that(output, contains_string("    z: str | None = None,\n"))
        # would appear if the signature got collapsed onto one line, like ast.unparse() does by default
        assert_that(output, not_(contains_string("def b[T](x: T")))

    def test_merges_into_an_existing_type_params_bracket(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify converting a second TypeVar merges it into an existing PEP 695 bracket instead of adding a new one."""
        # Regression test: a function that already declares one PEP 695 type parameter must gain
        # the new one inside the same bracket, not a second bracket next to it.
        subject = create_type_var_check("""
            from typing import TypeVar

            def f[U](x: U, y: T) -> T:
                return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def f[U, T](x: U, y: T) -> T:"))

    def test_converts_a_decorated_overload(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify converting a decorated @overload signature accounts for its non-zero-column indentation."""
        # A decorated function's "def" line isn't flush at column 0 like an undecorated one's -
        # it's a continuation line carrying its own real indentation.
        subject = create_type_var_check("""
            from typing import TypeVar, overload

            class Config:
                @overload
                def get(self, key: str, default: T = ...) -> T: ...
                def get(self, key: str, default: object = None) -> object:
                    return default

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("@overload"))
        assert_that(output, contains_string("def get[T](self, key: str, default: T = ...) -> T: ..."))

    def test_converts_two_type_params_sharing_one_import_without_corrupting_it(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
        """AI: Verify converting two names sharing one import leaves that import line untouched."""
        # Converting two names sharing one import must leave that import line untouched - the
        # recipe never edits it itself (ruff's F401 owns that).
        subject = create_type_var_check("""
            from typing import ParamSpec, TypeVar
            from collections.abc import Callable

            P = ParamSpec("P")
            T = TypeVar("T")

            def run_in_threadpool(func: Callable[P, T]) -> T:
                return func()

            def identity(x: T) -> T:
                return x
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("P", "fixed"))
        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        ast.parse(output)  # raises SyntaxError if the shared import got corrupted
        assert_that(output, contains_string("from typing import ParamSpec, TypeVar"))
        assert_that(output, not_(contains_string("P = ParamSpec")))
        assert_that(output, not_(contains_string("T = TypeVar")))

    def test_version_gate_below_pep695_reports_unsafe_with_reason(
        self, make_recipe: Callable[[type[PythonRefactoring], str], PythonRefactoring]
    ) -> None:
        """AI: Verify a target below the PEP 695 floor reports unsafe with the version-gate reason."""
        code = """
            from typing import TypeVar

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """
        subject = cast(TypeVarCheck, make_recipe(TypeVarCheck, code))
        subject.min_python_override = (3, 10)

        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.converted_unsafe_reasons, has_entry("T", UnsafeReason.PEP695_VERSION_GATE))
        assert_that(subject.apply_to_string(), contains_string('T = TypeVar("T")'))

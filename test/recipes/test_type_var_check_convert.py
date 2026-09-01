"""Tests for TypeVarCheck.convert_declared_typevars."""

import ast
from collections.abc import Callable

from hamcrest import assert_that, contains_string, has_entry, not_

from renaissance.refactoring.type_var_check import TypeVarCheck


class TestTypeVarCheckConvert:
    """See module docstring."""

    def test_converts_typevar_shared_across_functions_to_pep695(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
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
        assert_that(output, not_(contains_string("TypeVar")))

    def test_converts_typevar_shared_across_methods_to_pep695(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
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
        # Regression test for python-ast-known-limitations.md item 4: ast.unparse() plus
        # the rewrite pipeline's indentation correction used to double-indent a multi-line
        # docstring's continuation lines.
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
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar(\"T\")"))

    def test_does_not_convert_typevar_in_dunder_all(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
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
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar(\"T\")"))

    def test_removes_declaration_but_keeps_import_used_by_other_typevar(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
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
        assert_that(output, contains_string("U = TypeVar(\"U\")"))
        assert_that(output, not_(contains_string("T = TypeVar")))

    def test_converts_single_scope_typevar_without_ruff(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
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
        # Regression test: ast.unparse() can't represent comments at all (Python's ast module
        # never records them), so a whole-body replacement used to silently delete them - found
        # live against starlette/starlette/concurrency.py's _next(). Signature-only replacement
        # never regenerates the body, so this comment must survive untouched.
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

    def test_converts_function_preserving_unusual_body_formatting(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
        # Regression test: ast.unparse() reformats the whole body to its own style even though
        # only the signature changed - e.g. collapsing this multi-line call onto one line.
        # Signature-only replacement leaves the body's original bytes untouched.
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

    def test_does_not_add_redundant_type_param_to_nested_closure(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
        # Regression test: found live against starlette/starlette/authentication.py's requires()
        # and its nested websocket_wrapper/async_wrapper/sync_wrapper closures, which all
        # reference the outer function's ParamSpec in their own signatures too.
        # functions_using_nodes used to attribute that to the innermost enclosing function,
        # queuing a redundant, shadowing type param on the nested closure as well - which,
        # combined with the still-open rewrite dominance/suppression gap
        # (python-ast-known-limitations.md item 5), corrupted the output outright instead of
        # just being redundant.
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

    def test_converts_two_type_params_sharing_one_import_without_corrupting_it(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
        # Regression test for python-ast-known-limitations.md item 5: converting both T and P
        # used to queue two conflicting edits against their shared "from typing import ..." line,
        # corrupting it into "from typing import ParamSpecfrom typing import TypeVar".
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
        assert_that(output, not_(contains_string("typing import")))
        assert_that(output, not_(contains_string("TypeVar")))

"""Tests for TypeVarCheck.convert_declared_typevars."""

import ast
from collections.abc import Callable
from typing import cast

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entry, not_

from renaissance.recipes.python_refactoring import PythonRefactoring
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
        result = subject.check()

        assert_that(result["converted"], has_entry("T", "fixed"))
        assert_that(result["orphaned"], has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def a[T](x: T) -> T:"))
        assert_that(output, contains_string("def b[T](y: T) -> T:"))
        assert_that(output, not_(contains_string("T = TypeVar")))

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

    @pytest.mark.parametrize(
        ("extra_line", "imported_elsewhere", "expected_reason"),
        [
            pytest.param("class Box(Generic[T]): ...", frozenset(), UnsafeReason.USED_OUTSIDE_FUNCTION, id="generic-base"),
            pytest.param('__all__ = ["T"]', frozenset(), UnsafeReason.DECLARED_TYPEVAR_EXPORTED, id="exported-via-dunder-all"),
            pytest.param("", frozenset({"T"}), UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT, id="imported-elsewhere"),
        ],
    )
    def test_does_not_convert_unsafe_typevar(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        extra_line: str,
        imported_elsewhere: frozenset[str],
        expected_reason: UnsafeReason,
    ) -> None:
        """Verify a TypeVar that is_safe_to_convert rejects is reported unsafe with its reason and left unconverted."""
        subject = create_type_var_check(f"""
            from typing import Generic, TypeVar

            {extra_line}

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)
        subject.project_wide_imported_names = imported_elsewhere

        result = subject.convert_declared_typevars()

        assert_that(result, equal_to({"T": "unsafe"}))
        assert_that(subject.converted_unsafe_reasons, equal_to({"T": expected_reason}))
        assert_that(subject.apply_to_string(), contains_string("def a(x: T) -> T:"))

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

    def test_converts_function_using_two_new_type_params(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """Verify a function using two declared type parameters gets both in one bracket."""
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
        result = subject.check()

        assert_that(result["converted"], has_entry("P", "fixed"))
        assert_that(result["converted"], has_entry("T", "fixed"))
        assert_that(result["orphaned"], equal_to({"P": "fixed", "T": "fixed"}))
        functions = {node.name: node for node in ast.parse(subject.apply_to_string()).body if isinstance(node, ast.FunctionDef)}
        assert_that([param.name for param in functions["run_in_threadpool"].type_params], equal_to(["P", "T"]))
        assert_that([param.name for param in functions["identity"].type_params], equal_to(["T"]))

    def test_orders_type_params_by_declaration(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """Verify the added type parameters follow the order their declarations appear in the file."""
        names = ["A", "B", "C", "D", "E", "F"]
        declarations = "\n".join(f'{name} = TypeVar("{name}")' for name in names)
        parameters = ", ".join(f"{name.lower()}: {name}" for name in names)
        subject = create_type_var_check(f"from typing import TypeVar\n{declarations}\ndef f({parameters}) -> None: ...\n")

        subject.convert_declared_typevars()

        assert_that(subject.apply_to_string(), contains_string(f"def f[{', '.join(names)}]({parameters}) -> None: ..."))

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
        subject.min_python = (3, 10)

        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.converted_unsafe_reasons, has_entry("T", UnsafeReason.PEP695_VERSION_GATE))
        assert_that(subject.apply_to_string(), contains_string('T = TypeVar("T")'))

    @pytest.mark.xfail(
        reason="_renormalize_indent takes the body's minimum indent over every line, including the lines "
        "inside a multi-line string literal, so the literal's value changes.",
        raises=AssertionError,
        strict=True,
    )
    def test_converts_function_preserving_multiline_string_literal(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """Verify converting a function keeps a multi-line string literal whose continuation line is at column 0."""
        # Built line by line: textwrap.dedent in the fixture would otherwise be blocked by the column-0 line.
        source_lines = [
            "from typing import TypeVar",
            'T = TypeVar("T")',
            "def f(x: T) -> T:",
            '    text = """first',
            "second",
            '    third"""',
            "    return x",
        ]
        subject = create_type_var_check("\n".join(source_lines) + "\n")
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def f[T](x: T) -> T:"))
        text_assign = next(
            node for node in ast.walk(ast.parse(output)) if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == "text"
        )
        assert_that(ast.literal_eval(text_assign.value), equal_to("first\nsecond\n    third"))

    @pytest.mark.parametrize(
        ("class_header", "expected_result", "expected_reasons", "expected_method"),
        [
            pytest.param(
                "class Box[T]:",
                {"T": "unsafe"},
                {"T": UnsafeReason.USED_IN_PEP695_CLASS},
                "def get(self, x: T) -> T:",
                id="class-declares-the-name",
            ),
            pytest.param("class Box[U]:", {"T": "fixed"}, {}, "def get[T](self, x: T) -> T:", id="class-declares-another-name"),
        ],
    )
    def test_does_not_convert_typevar_used_in_pep695_class(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        class_header: str,
        expected_result: dict[str, str],
        expected_reasons: dict[str, UnsafeReason],
        expected_method: str,
    ) -> None:
        """Verify a name a PEP 695 class already declares is left alone inside it, while other names still convert."""
        subject = create_type_var_check(f"""
            from typing import TypeVar
            T = TypeVar('T')

            {class_header}
                def get(self, x: T) -> T:
                    return x
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, equal_to(expected_result))
        assert_that(subject.converted_unsafe_reasons, equal_to(expected_reasons))
        assert_that(subject.apply_to_string(), contains_string(expected_method))

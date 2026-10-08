"""Tests for TypeVarCheck.convert_declared_typevars."""

import ast
from collections.abc import Callable
from typing import cast

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entry, not_

from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.type_var_check import PEP_695_MINIMUM, PEP_696_MINIMUM, TypeVarCheck
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
        # For example a Sphinx ".. seealso::" block.
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

    @pytest.mark.parametrize(
        ("extra_line", "imported_elsewhere"),
        [
            pytest.param('__all__ = ["T"]', frozenset(), id="exported-via-dunder-all"),
            pytest.param("", frozenset({"T"}), id="imported-elsewhere"),
        ],
    )
    def test_converts_functions_using_a_typevar_whose_declaration_must_stay(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        extra_line: str,
        imported_elsewhere: frozenset[str],
    ) -> None:
        """Verify functions get [T] even when T's declaration can't be removed, and the declaration is kept."""
        subject = create_type_var_check(f"""
            from typing import TypeVar

            {extra_line}

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)
        subject.project_wide_imported_names = imported_elsewhere

        result = subject.convert_declared_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def a[T](x: T) -> T:"))
        assert_that(output, contains_string('T = TypeVar("T")'))

    def test_converts_function_preserving_unusual_body_formatting(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify converting a signature never reformats or collapses its body's unusual formatting."""
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
        # PEP 695 type parameters are already visible in nested scopes.
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
        "class_header",
        [
            pytest.param("class Box(Generic[T]):", id="generic-base"),
            pytest.param("class Box(Protocol[T]):", id="protocol-base"),
            pytest.param("class Sub(Base[T]):", id="generic-subclass"),
            pytest.param("class Box[T]:", id="pep695-class"),
        ],
    )
    def test_converts_function_but_not_methods_of_a_generic_class(
        self, create_type_var_check: Callable[[str], TypeVarCheck], class_header: str
    ) -> None:
        """Verify a standalone function gets [T] while the methods of a class generic over T keep using the class's T."""
        subject = create_type_var_check(f"""
            from typing import Generic, Protocol, TypeVar
            T = TypeVar('T')

            {class_header}
                def get(self, x: T) -> T:
                    return x

            def first(items: list[T]) -> T:
                return items[0]
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def first[T](items: list[T]) -> T:"))
        assert_that(output, contains_string("    def get(self, x: T) -> T:"))

    @pytest.mark.parametrize(
        "class_header",
        [
            pytest.param("class Box(Generic[T]):", id="generic-base"),
            pytest.param("class Box[T]:", id="pep695-class"),
        ],
    )
    def test_reports_typevar_used_only_in_a_generic_class(
        self, create_type_var_check: Callable[[str], TypeVarCheck], class_header: str
    ) -> None:
        """Verify a TypeVar only a generic class uses is reported unsafe with its reason and left as it is."""
        subject = create_type_var_check(f"""
            from typing import Generic, TypeVar
            T = TypeVar('T')

            {class_header}
                def get(self, x: T) -> T:
                    return x
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, equal_to({"T": "unsafe"}))
        assert_that(subject.converted_unsafe_reasons, equal_to({"T": UnsafeReason.USED_IN_GENERIC_CLASS}))
        assert_that(subject.apply_to_string(), contains_string("    def get(self, x: T) -> T:"))

    @pytest.mark.parametrize(
        "class_header",
        [
            pytest.param("class Util:", id="plain-class"),
            pytest.param("class Box(Generic[U]):", id="generic-over-another-name"),
            pytest.param("class Box[U]:", id="pep695-class-over-another-name"),
        ],
    )
    def test_converts_method_of_a_class_not_generic_over_the_name(
        self, create_type_var_check: Callable[[str], TypeVarCheck], class_header: str
    ) -> None:
        """Verify a method gets [T] when its class isn't generic over T."""
        subject = create_type_var_check(f"""
            from typing import Generic, TypeVar
            T = TypeVar('T')
            U = TypeVar('U')

            {class_header}
                def get(self, x: T) -> T:
                    return x
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("    def get[T](self, x: T) -> T:"))

    def test_converts_function_when_typevar_is_also_used_outside_functions(
        self, create_type_var_check: Callable[[str], TypeVarCheck]
    ) -> None:
        """Verify a function using T is converted even though a module-level alias also uses T."""
        subject = create_type_var_check("""
            from typing import TypeVar
            T = TypeVar('T')

            Pair = tuple[T, T]

            def first(pair: Pair) -> T:
                return pair[0]

            def same(x: T) -> T:
                return x
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        assert_that(subject.apply_to_string(), contains_string("def same[T](x: T) -> T:"))


_HEADER = "from collections.abc import Callable\nfrom typing import ParamSpec, TypeVar, TypeVarTuple, Unpack\n\n"
_TYPEVAR_USE = "def a(x: T) -> T:"
_PARAMSPEC_USE = "def a(f: Callable[P, int]) -> Callable[P, int]:"
_TYPEVARTUPLE_USE = "def a(*args: *Ts) -> tuple[*Ts]:"


def _source(declarations: str, signature: str) -> str:
    """Build a module with the given legacy declarations and a single function using them."""
    return f"{_HEADER}{declarations}\n\n\n{signature}\n    ...\n"


class TestTypeVarCheckConvertArguments:
    """Every constructor argument is carried over or refused with a reason, never lost silently."""

    @pytest.mark.parametrize(
        ("declaration", "signature", "expected_signature"),
        [
            pytest.param('T = TypeVar("T")', _TYPEVAR_USE, "def a[T](x: T) -> T:", id="typevar-plain"),
            pytest.param('T = TypeVar("T", int, str)', _TYPEVAR_USE, "def a[T: (int, str)](x: T) -> T:", id="typevar-constraints"),
            pytest.param('T = TypeVar("T", bound=int)', _TYPEVAR_USE, "def a[T: int](x: T) -> T:", id="typevar-bound"),
            pytest.param('T = TypeVar("T", default=int)', _TYPEVAR_USE, "def a[T = int](x: T) -> T:", id="typevar-default"),
            pytest.param(
                'T = TypeVar("T", bound=str, default=str)',
                _TYPEVAR_USE,
                "def a[T: str = str](x: T) -> T:",
                id="typevar-bound-default",
            ),
            pytest.param(
                'T = TypeVar("T", int, str, default=int)',
                _TYPEVAR_USE,
                "def a[T: (int, str) = int](x: T) -> T:",
                id="typevar-constraints-default",
            ),
            pytest.param('T = TypeVar("T", infer_variance=True)', _TYPEVAR_USE, "def a[T](x: T) -> T:", id="typevar-infer-variance"),
            pytest.param(
                'P = ParamSpec("P")',
                _PARAMSPEC_USE,
                "def a[**P](f: Callable[P, int]) -> Callable[P, int]:",
                id="paramspec-plain",
            ),
            pytest.param(
                'P = ParamSpec("P", default=[int, str])',
                _PARAMSPEC_USE,
                "def a[**P = [int, str]](f: Callable[P, int]) -> Callable[P, int]:",
                id="paramspec-default",
            ),
            pytest.param('Ts = TypeVarTuple("Ts")', _TYPEVARTUPLE_USE, "def a[*Ts](*args: *Ts) -> tuple[*Ts]:", id="typevartuple-plain"),
            pytest.param(
                'Ts = TypeVarTuple("Ts", default=Unpack[tuple[int]])',
                _TYPEVARTUPLE_USE,
                "def a[*Ts = Unpack[tuple[int]]](*args: *Ts) -> tuple[*Ts]:",
                id="typevartuple-default",
            ),
        ],
    )
    def test_converts_keeping_every_expressible_argument(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        declaration: str,
        signature: str,
        expected_signature: str,
    ) -> None:
        """Verify bounds, constraints, defaults and inferred variance are carried over."""
        name = declaration.split(" = ", maxsplit=1)[0]
        subject = create_type_var_check(_source(declaration, signature))
        subject.min_python = PEP_696_MINIMUM

        result = subject.convert_declared_typevars()

        assert_that(result, has_entry(name, "fixed"))
        output = subject.apply_to_string()
        ast.parse(output)
        assert_that(output, contains_string(expected_signature))

    @pytest.mark.parametrize(
        ("declaration", "signature", "min_python", "expected_reason"),
        [
            pytest.param(
                'T = TypeVar("T", default=int)',
                _TYPEVAR_USE,
                PEP_695_MINIMUM,
                UnsafeReason.PEP696_VERSION_GATE,
                id="typevar-default-3.12",
            ),
            pytest.param(
                'P = ParamSpec("P", default=[int, str])',
                _PARAMSPEC_USE,
                PEP_695_MINIMUM,
                UnsafeReason.PEP696_VERSION_GATE,
                id="paramspec-default-3.12",
            ),
            pytest.param(
                'Ts = TypeVarTuple("Ts", default=Unpack[tuple[int]])',
                _TYPEVARTUPLE_USE,
                PEP_695_MINIMUM,
                UnsafeReason.PEP696_VERSION_GATE,
                id="typevartuple-default-3.12",
            ),
            pytest.param(
                'T = TypeVar("T", covariant=True)',
                _TYPEVAR_USE,
                PEP_696_MINIMUM,
                UnsafeReason.NO_PEP695_EQUIVALENT,
                id="typevar-covariant",
            ),
            pytest.param(
                'T = TypeVar("T", contravariant=True)',
                _TYPEVAR_USE,
                PEP_696_MINIMUM,
                UnsafeReason.NO_PEP695_EQUIVALENT,
                id="typevar-contravariant",
            ),
            pytest.param(
                'P = ParamSpec("P", covariant=True)',
                _PARAMSPEC_USE,
                PEP_696_MINIMUM,
                UnsafeReason.NO_PEP695_EQUIVALENT,
                id="paramspec-covariant",
            ),
            pytest.param(
                'Ts = TypeVarTuple("Ts", bound=int, covariant=True)',
                _TYPEVARTUPLE_USE,
                PEP_696_MINIMUM,
                UnsafeReason.NO_PEP695_EQUIVALENT,
                id="typevartuple-bound-covariant",
            ),
            pytest.param(
                'P = ParamSpec("P", bound=int)',
                _PARAMSPEC_USE,
                PEP_696_MINIMUM,
                UnsafeReason.NO_PEP695_EQUIVALENT,
                id="paramspec-bound",
            ),
            pytest.param(
                'T = TypeVar("T", future_kw=1)',
                _TYPEVAR_USE,
                PEP_696_MINIMUM,
                UnsafeReason.NO_PEP695_EQUIVALENT,
                id="unknown-keyword",
            ),
            pytest.param(
                'T = TypeVar("T", **options)',
                _TYPEVAR_USE,
                PEP_696_MINIMUM,
                UnsafeReason.NO_PEP695_EQUIVALENT,
                id="double-star-keywords",
            ),
        ],
    )
    def test_refuses_argument_it_cannot_carry_over(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        declaration: str,
        signature: str,
        min_python: tuple[int, int],
        expected_reason: UnsafeReason,
    ) -> None:
        """Verify an argument the target can't express is reported unsafe with its reason and the file is left unchanged."""
        name = declaration.split(" = ", maxsplit=1)[0]
        source = _source(declaration, signature)
        subject = create_type_var_check(source)
        subject.min_python = min_python

        result = subject.convert_declared_typevars()

        assert_that(result, has_entry(name, "unsafe"))
        assert_that(subject.converted_unsafe_reasons, has_entry(name, expected_reason))
        assert_that(subject.apply_to_string(), equal_to(source))

    @pytest.mark.parametrize(
        ("declarations", "signature", "expected_signature"),
        [
            pytest.param(
                'T = TypeVar("T", default=int)\nU = TypeVar("U")',
                "def f(x: T, y: U) -> T:",
                "def f[U, T = int](x: T, y: U) -> T:",
                id="defaulted-declared-first",
            ),
            pytest.param(
                'U = TypeVar("U")',
                "def f[T = int](x: T, y: U) -> T:",
                "def f[U, T = int](x: T, y: U) -> T:",
                id="existing-defaulted-param",
            ),
            pytest.param(
                'T = TypeVar("T", default=int)\nTs = TypeVarTuple("Ts")',
                "def f(x: T, *args: *Ts) -> T:",
                "def f[*Ts, T = int](x: T, *args: *Ts) -> T:",
                id="typevartuple-after-defaulted",
            ),
        ],
    )
    def test_places_defaulted_type_params_last(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        declarations: str,
        signature: str,
        expected_signature: str,
    ) -> None:
        """Verify type parameters with a default come after those without one, which Python requires."""
        subject = create_type_var_check(_source(declarations, signature))
        subject.min_python = PEP_696_MINIMUM

        subject.convert_declared_typevars()

        output = subject.apply_to_string()
        ast.parse(output)
        assert_that(output, contains_string(expected_signature))

    @pytest.mark.xfail(
        reason="A default referencing another legacy declaration is carried over as is, so the new type "
        "parameter's default refers to the module-level TypeVar.",
        raises=AssertionError,
        strict=True,
    )
    def test_does_not_convert_default_referencing_another_declaration(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
    ) -> None:
        """Verify a declaration whose default uses another legacy type parameter is reported unsafe and left unconverted."""
        subject = create_type_var_check(_source('T = TypeVar("T")\nU = TypeVar("U", default=T)', "def f(x: U) -> U:"))
        subject.min_python = PEP_696_MINIMUM

        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("U", "unsafe"))
        assert_that(subject.converted_unsafe_reasons, has_entry("U", not_(UnsafeReason.PEP696_VERSION_GATE)))
        assert_that(subject.apply_to_string(), contains_string("def f(x: U) -> U:"))

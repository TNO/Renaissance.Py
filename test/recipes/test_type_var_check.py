import textwrap
from pathlib import Path

import pytest
from hamcrest import assert_that, contains_string, has_entry, has_key, is_, is_not, not_  # pyright: ignore[reportUnknownVariableType]
from pytest_mock import MockerFixture
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.type_var_check import PEP_695_MINIMUM, TypeVarCheck, target_supports_pep695

class TestTypeVarCheck:

    def _create(self, mocker: MockerFixture, text: str) -> TypeVarCheck:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code),
        )
        subject = TypeVarCheck("x.py")
        subject.in_memory = True
        # These tests exercise other behaviour, not version gating - assume 3.12+ so they
        # don't depend on whatever pyproject.toml happens to be found from the ambient cwd.
        subject.min_python_override = PEP_695_MINIMUM
        return subject

    def _create_cross_file(
        self, mocker: MockerFixture, tmp_path: Path, origin_text: str, importing_text: str
    ) -> TypeVarCheck:
        (tmp_path / "file_1.py").write_text(textwrap.dedent(origin_text))

        importing_code = textwrap.dedent(importing_text)
        importing_file = str(tmp_path / "file_2.py")
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(importing_code, importing_file),
        )
        subject = TypeVarCheck(importing_file)
        subject.in_memory = True
        subject.min_python_override = PEP_695_MINIMUM
        return subject

    def test_typevar_used_in_multiple_functions(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
            class Foo:
                def a(self: T) -> T:
                    return self
                def b(self: T) -> T:
                    return self

            T = TypeVar("T")
        """)
        result = subject.find_multi_scope_typevars()
        assert_that(result, has_key("T"))

    def test_typevar_used_in_single_function_not_flagged(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)
        result = subject.find_multi_scope_typevars()
        assert_that(result, is_not(has_key("T")))

    @pytest.mark.parametrize("code,name,should_flag", [
        (
            """
            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y
            def c(z: T) -> T:
                return z

            T = TypeVar("T")
            """,
            "T",
            True,
        ),
        (
            """
            def a(x: T, y: T) -> T:
                return x

            T = TypeVar("T")
            """,
            "T",
            False,
        ),
        (
            """
            def a(x: T) -> T:
                return x
            def b(y: U) -> U:
                return y
            def c(z: U) -> U:
                return z

            T = TypeVar("T")
            U = TypeVar("U")
            """,
            "T",
            False,
        ),
        (
            """
            def a(x: T) -> T:
                return x
            def b(y: U) -> U:
                return y
            def c(z: U) -> U:
                return z

            T = TypeVar("T")
            U = TypeVar("U")
            """,
            "U",
            True,
        ),
        (
            """
            def a(x: int) -> int:
                return x
            """,
            "T",
            False,
        ),
        (
            """
            def a(x: P) -> P:
                return x
            def b(y: P) -> P:
                return y
            def c(z: P) -> P:
                return z

            P = ParamSpec("P")
            """,
            "P",
            True,
        ),
        (
            """
            def a(*args: *Ts) -> tuple[*Ts]:
                return args
            def b(*args: *Ts) -> tuple[*Ts]:
                return args

            Ts = TypeVarTuple("Ts")
            """,
            "Ts",
            True,
        )
    ])
    def test_multi_scope_detection_cases(self, mocker: MockerFixture, code: str, name: str, should_flag: bool) -> None:
        subject = self._create(mocker, code)
        result = subject.find_multi_scope_typevars()
        if should_flag:
            assert_that(result, has_key(name))
        else:
            assert_that(result, is_not(has_key(name)))

    def test_localizes_plain_function_generic_typevar(self, mocker: MockerFixture, tmp_path: Path) -> None:
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """,
            """
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))
        assert_that(subject.apply_to_string(), not_(contains_string("from file_1 import T")))

    def test_does_not_localize_typevar_in_dunder_all(self, mocker: MockerFixture, tmp_path: Path) -> None:
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            __all__ = ["T"]
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """,
            """
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.apply_to_string(), contains_string("from file_1 import T"))

    def test_does_not_localize_typevar_used_in_exported_generic_base(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar, Generic
            T = TypeVar("T")
            class Box(Generic[T]):
                pass
            """,
            """
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.apply_to_string(), contains_string("from file_1 import T"))

    def test_keeps_other_names_when_localizing_one_of_several_imports(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            T = TypeVar("T")
            def helper() -> None:
                pass
            """,
            """
            from file_1 import T, helper
            def b(x: T) -> T:
                helper()
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("from file_1 import helper"))
        assert_that(output, contains_string("T = TypeVar('T')"))

    def test_adds_missing_typevar_import_when_localizing(self, mocker: MockerFixture, tmp_path: Path) -> None:
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """,
            """
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("from typing import TypeVar"))

    def test_does_not_duplicate_already_present_typevar_import(self, mocker: MockerFixture, tmp_path: Path) -> None:
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """,
            """
            from typing import TypeVar
            from file_1 import T
            U = TypeVar("U")
            def b(x: T) -> T:
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output.count("from typing import TypeVar"), is_(1))

    def test_no_typevar_import_found(self, mocker: MockerFixture, tmp_path: Path) -> None:
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            def helper() -> None:
                pass
            """,
            """
            from file_1 import helper
            def b() -> None:
                helper()
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, is_({}))

    def test_converts_typevar_shared_across_functions_to_pep695(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_converts_typevar_shared_across_methods_to_pep695(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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
        self, mocker: MockerFixture
    ) -> None:
        # Regression test for python-ast-known-limitations.md item 5: ast.unparse() plus
        # the rewrite pipeline's indentation correction used to double-indent a multi-line
        # docstring's continuation lines.
        subject = self._create(mocker, """
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

    def test_converts_function_with_nested_docstring_indentation(self, mocker: MockerFixture) -> None:
        # A docstring with an internal nested block (e.g. Sphinx's ".. seealso::") must keep
        # that block's *relative* extra indentation, not get flattened to one uniform level.
        subject = self._create(mocker, """
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

    def test_converts_function_with_single_line_docstring(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_converts_bound_typevar(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_converts_constrained_typevar(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_converts_paramspec(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_converts_typevartuple(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_does_not_convert_typevar_used_in_generic_base(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_does_not_convert_typevar_in_dunder_all(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_removes_declaration_but_keeps_import_used_by_other_typevar(self, mocker: MockerFixture) -> None:
        # T is multi-scope and safe to convert; U is left alone (used in a Generic[...] base),
        # so the shared "from typing import TypeVar" import must survive for U's sake.
        subject = self._create(mocker, """
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

    def test_removes_orphaned_declaration_after_manual_or_ruff_pep695_conversion(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_removes_fully_unused_declaration(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
            from typing import TypeVar
            T = TypeVar('T')

            def b() -> None:
                pass
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), not_(contains_string("TypeVar")))

    def test_does_not_touch_declaration_still_live_outside_shadow(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
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

    def test_does_not_remove_declaration_used_in_generic_base(self, mocker: MockerFixture) -> None:
        # The Generic[T] base is a real, non-shadowed use, so this is never even flagged -
        # same as any other still-live declaration.
        subject = self._create(mocker, """
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

    def test_does_not_remove_orphaned_declaration_in_dunder_all(self, mocker: MockerFixture) -> None:
        # Every reference is shadowed, but T is still exported public API via __all__, so
        # removing the declaration would break importers - flagged "unsafe", not silently fixed.
        subject = self._create(mocker, """
            from typing import TypeVar

            __all__ = ["T"]

            T = TypeVar('T')

            def b[T](x: T) -> T:
                return x
        """)
        result = subject.remove_orphaned_declarations()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.apply_to_string(), contains_string("T = TypeVar('T')"))

    def test_check_cleans_up_ruff_style_leftover_end_to_end(self, mocker: MockerFixture) -> None:
        # Caught directly by phase 2 (convert_declared_typevars skips the already-shadowed
        # function and just drops the now-redundant declaration) - "orphaned" (phase 3) is
        # a defensive no-op here, exercised separately by test_removes_orphaned_declaration_*.
        subject = self._create(mocker, """
            from typing import TypeVar
            T = TypeVar('T')

            def b[T](x: T) -> T:
                return x
        """)
        subject.run()

        assert_that(subject.result["converted"], has_entry("T", "fixed"))
        assert_that(subject.result["orphaned"], is_({}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))
        assert_that(output, not_(contains_string("TypeVar")))

    def test_converts_single_scope_typevar_without_ruff(self, mocker: MockerFixture) -> None:
        subject = self._create(mocker, """
            from typing import TypeVar

            T = TypeVar('T')

            def b(x: T) -> T:
                return x
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))
        assert_that(output, not_(contains_string("TypeVar")))

    def test_check_localizes_converts_and_removes_import_in_one_pass(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """,
            """
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )
        subject.run()

        assert_that(subject.result["cross_file"], has_entry("T", "fixed"))
        assert_that(subject.result["converted"], has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("def b[T](x: T) -> T:"))
        assert_that(output, not_(contains_string("TypeVar")))
        assert_that(output, not_(contains_string("import")))

    def _create_versioned(
        self, mocker: MockerFixture, tmp_path: Path, requires_python: str | None, code: str
    ) -> TypeVarCheck:
        if requires_python is not None:
            (tmp_path / "pyproject.toml").write_text(f'[project]\nrequires-python = "{requires_python}"\n')
        file_path = str(tmp_path / "subject.py")
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(textwrap.dedent(code), file_path),
        )
        subject = TypeVarCheck(file_path)
        subject.in_memory = True
        return subject

    # target_supports_pep695() is a thin wrapper around minimum_python_version() (see
    # test/utils/test_python_version.py for the deep coverage of pyproject.toml lookup and
    # requires-python parsing) - these two just confirm it applies the >=(3, 12) threshold.
    def test_target_supports_pep695_true_for_3_12_plus(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.12"\n')
        assert_that(target_supports_pep695(str(tmp_path / "file.py")), is_(True))

    def test_target_supports_pep695_false_for_3_10(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.10"\n')
        assert_that(target_supports_pep695(str(tmp_path / "file.py")), is_(False))

    def test_convert_declared_typevars_reports_unsafe_when_target_too_old(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        subject = self._create_versioned(mocker, tmp_path, ">=3.10", """
            from typing import TypeVar

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.apply_to_string(), contains_string('T = TypeVar("T")'))

    def test_convert_declared_typevars_still_fixes_when_target_new_enough(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        subject = self._create_versioned(mocker, tmp_path, ">=3.12", """
            from typing import TypeVar

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """)
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("def a[T](x: T) -> T:"))

    def test_check_still_localizes_when_target_too_old(self, mocker: MockerFixture, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.10"\n')
        (tmp_path / "file_1.py").write_text(textwrap.dedent("""
            from typing import TypeVar
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """))
        importing_file = str(tmp_path / "file_2.py")
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(
                textwrap.dedent("""
                    from file_1 import T
                    def b(x: T) -> T:
                        return x
                    """),
                importing_file,
            ),
        )
        subject = TypeVarCheck(importing_file)
        subject.in_memory = True
        subject.run()

        assert_that(subject.result["cross_file"], has_entry("T", "fixed"))
        assert_that(subject.result["converted"], has_entry("T", "unsafe"))
        output = subject.apply_to_string()
        assert_that(output, contains_string('T = TypeVar(\'T\')'))
        assert_that(output, not_(contains_string("def b[T]")))
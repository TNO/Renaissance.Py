"""Tests for TypeVarCheck.localize_imported_typevars."""

import textwrap
from pathlib import Path

from hamcrest import assert_that, contains_string, has_entry, is_, not_
from pytest_mock import MockerFixture

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.type_var_check import PEP_695_MINIMUM, TypeVarCheck


class TestTypeVarCheckLocalize:
    """See module docstring."""

    def _create_cross_file(self, mocker: MockerFixture, tmp_path: Path, origin_text: str, importing_text: str) -> TypeVarCheck:
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

    def test_does_not_localize_typevar_used_in_exported_generic_base(self, mocker: MockerFixture, tmp_path: Path) -> None:
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

    def test_keeps_other_names_when_localizing_one_of_several_imports(self, mocker: MockerFixture, tmp_path: Path) -> None:
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

    def test_check_localizes_converts_and_removes_import_in_one_pass(self, mocker: MockerFixture, tmp_path: Path) -> None:
        # Whole-pipeline integration, grouped here since cross-file localization is what
        # sets this case apart from the plain-conversion tests in test_type_var_check_convert.py.
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

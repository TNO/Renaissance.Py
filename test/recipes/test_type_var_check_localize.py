"""Tests for TypeVarCheck.localize_imported_typevars."""

import ast
import builtins
import textwrap
from pathlib import Path
from typing import cast

import pytest
from hamcrest import assert_that, contains_string, equal_to, has_entry, is_, not_
from pytest_mock import MockerFixture

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.type_var_check import PEP_695_MINIMUM, TypeVarCheck
from renaissance.recipes.type_var_domain import UnsafeReason


def _module_level_names(module: ast.Module) -> set[str]:
    """Return the names bound at module level by imports, classes, functions and assignments."""
    names: set[str] = set()
    for node in module.body:
        if isinstance(node, ast.Import | ast.ImportFrom):
            names.update((alias.asname or alias.name).split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return names


def _names_used_by(call: ast.Call) -> set[str]:
    """Return the non-builtin names a TypeVar call's arguments use, including inside string forward references."""
    names: set[str] = set()
    for argument in [*call.args[1:], *(keyword.value for keyword in call.keywords)]:
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            argument = ast.parse(argument.value, mode="eval").body
        names.update(node.id for node in ast.walk(argument) if isinstance(node, ast.Name))
    return names - set(dir(builtins))


class TestTypeVarCheckLocalize:
    """See module docstring."""

    def _create_cross_file(self, mocker: MockerFixture, tmp_path: Path, origin_text: str, importing_text: str) -> TypeVarCheck:
        """Write origin_text to file_1.py and return an in-memory TypeVarCheck on file_2.py holding importing_text."""
        (tmp_path / "file_1.py").write_text(textwrap.dedent(origin_text))

        importing_code = textwrap.dedent(importing_text)
        importing_file = str(tmp_path / "file_2.py")
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(importing_code, importing_file),
        )
        subject = TypeVarCheck(importing_file)
        subject.in_memory = True
        subject.min_python = PEP_695_MINIMUM
        return subject

    def test_localizes_plain_function_generic_typevar(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify an imported TypeVar used only inside a plain function localizes into the importing file."""
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

    @pytest.mark.parametrize(
        "origin_extra",
        [
            pytest.param('__all__ = ["T"]', id="origin-exports-it"),
            pytest.param("class Box(Generic[T]):\n    pass", id="origin-class-is-generic-over-it"),
        ],
    )
    def test_localizes_typevar_whatever_its_origin_does_with_it(self, mocker: MockerFixture, tmp_path: Path, origin_extra: str) -> None:
        """Verify an imported TypeVar is localized even when its origin exports it or has a class generic over it."""
        origin = f"from typing import Generic, TypeVar\nT = TypeVar('T')\n{origin_extra}\n"
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            origin,
            """
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("T = TypeVar('T')"))
        assert_that(output, not_(contains_string("from file_1 import T")))

    @pytest.mark.parametrize(
        "declaration",
        [
            pytest.param('T = TypeVar("T", bound=Shape)', id="invariant-bound"),
            pytest.param('T = TypeVar("T", int, Shape)', id="constraints"),
            pytest.param('T = TypeVar("T", bound=Shape, covariant=True)', id="covariant"),
            pytest.param('T = TypeVar("T", bound=Shape, contravariant=True)', id="contravariant"),
            pytest.param('T = TypeVar("T", bound="Shape")', id="string-bound"),
        ],
    )
    def test_localized_declaration_keeps_its_meaning(self, mocker: MockerFixture, tmp_path: Path, declaration: str) -> None:
        """Verify the local copy has the origin's exact arguments and every name they use is defined in the importing file."""
        origin = f"from typing import TypeVar\nclass Shape:\n    pass\n{declaration}\n"
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            origin,
            """
            from file_1 import T
            def biggest(items: list[T]) -> T:
                return items[0]
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        module = ast.parse(subject.apply_to_string())
        local_call = next(node.value for node in module.body if isinstance(node, ast.Assign))
        origin_call = cast("ast.Assign", ast.parse(origin).body[-1]).value
        assert_that(ast.dump(local_call), equal_to(ast.dump(origin_call)))
        assert_that(_names_used_by(cast("ast.Call", local_call)) - _module_level_names(module), equal_to(set()))

    @pytest.mark.parametrize(
        ("origin", "importing_extra"),
        [
            pytest.param(
                'from typing import TypeVar\nclass Shape:\n    pass\nT = TypeVar("T", bound=Shape)\n',
                "class Shape:\n    pass",
                id="name-means-something-else-here",
            ),
            pytest.param(
                "from typing import TYPE_CHECKING, TypeVar\n"
                "if TYPE_CHECKING:\n"
                "    from shapes import Shape\n"
                'T = TypeVar("T", bound="Shape")\n',
                "",
                id="origin-binds-it-only-for-type-checking",
            ),
        ],
    )
    def test_does_not_localize_when_a_name_the_declaration_uses_cant_be_imported_safely(
        self, mocker: MockerFixture, tmp_path: Path, origin: str, importing_extra: str
    ) -> None:
        """Verify a declaration using a name that can't be imported from the origin as the same object stays imported."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            origin,
            f"from file_1 import T\n{importing_extra}\ndef biggest(items: list[T]) -> T:\n    return items[0]\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "unsafe"}))
        assert_that(subject.cross_file_unsafe_reasons, equal_to({"T": UnsafeReason.DECLARATION_NAME_UNAVAILABLE}))
        assert_that(subject.apply_to_string(), contains_string("from file_1 import T"))

    @pytest.mark.parametrize(
        ("dunder_all", "imported_elsewhere"),
        [
            pytest.param('__all__ = ["T"]', frozenset(), id="re-exported-via-dunder-all"),
            pytest.param("", frozenset({"T"}), id="imported-from-here-elsewhere"),
        ],
    )
    def test_localizes_typevar_this_file_re_exports(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        dunder_all: str,
        imported_elsewhere: frozenset[str],
    ) -> None:
        """Verify an imported TypeVar is localized even when this file passes it on to others."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            T = TypeVar("T")
            """,
            f"""
            from file_1 import T
            {dunder_all}
            def b(x: T) -> T:
                return x
            """,
        )
        subject.project_wide_imported_names = imported_elsewhere

        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, contains_string("T = TypeVar('T')"))
        assert_that(output, not_(contains_string("from file_1 import T")))

    def test_keeps_other_names_when_localizing_one_of_several_imports(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify localizing one imported name from a multi-name import statement keeps the other names imported."""
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

    @pytest.mark.xfail(
        reason="localize_imported_typevars queues one replace per localized name on the same import "
        "statement, which the rewriter rejects as conflicting rewrites.",
        raises=ValueError,
        strict=True,
    )
    def test_localizes_two_names_from_one_import_statement(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Verify one import statement bringing in two localizable names localizes both."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            T = TypeVar("T")
            U = TypeVar("U")
            """,
            """
            from file_1 import T, U
            def b(x: T, y: U) -> T:
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(result, has_entry("U", "fixed"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("T = TypeVar('T')"))
        assert_that(output, contains_string("U = TypeVar('U')"))
        assert_that(output, not_(contains_string("from file_1 import")))

    def test_adds_missing_typevar_import_when_localizing(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify localizing a TypeVar adds the "from typing import TypeVar" import if missing."""
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
        """AI: Verify localizing a TypeVar doesn't add a duplicate "from typing import TypeVar" when one already exists."""
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

    def test_localizes_when_origin_brings_typevar_into_scope_via_wildcard_import(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        """AI: Verify localizing still succeeds when the origin brings TypeVar into scope via a wildcard import."""
        # find_import_source can't locate "TypeVar" here - safe only because the importing file
        # already imports it itself.
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import *
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """,
            """
            from typing import TypeVar
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output.count("from typing import TypeVar"), is_(1))

    def test_does_not_localize_when_origin_imports_constructor_conditionally(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        """A TypeVar whose origin picks TypeVar per Python version stays imported, marked unsafe."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            import sys
            if sys.version_info >= (3, 13):
                from typing import TypeVar
            else:
                from typing_extensions import TypeVar
            T = TypeVar("T", contravariant=True, default=None)
            """,
            """
            from typing import TypeVar
            from file_1 import T, helper
            def b(x: T) -> None:
                helper()
            """,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(
            subject.cross_file_unsafe_reasons,
            has_entry("T", UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY),
        )
        output = subject.apply_to_string()
        assert_that(output, contains_string("from file_1 import T, helper"))
        assert_that(output, not_(contains_string("T = TypeVar")))

    def test_unparsable_origin_error_names_the_origin_file(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Verify a syntax error in the origin module is raised with the origin file's path, not `<unknown>`."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            """
            from typing import TypeVar
            T = TypeVar("T")
            def broken(:
            """,
            """
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )

        with pytest.raises(SyntaxError) as excinfo:
            subject.localize_imported_typevars()

        assert_that(excinfo.value.filename, is_(str(tmp_path / "file_1.py")))

    def test_no_typevar_import_found(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify localize_imported_typevars reports nothing when the importing file has no cross-file TypeVar."""
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

    def test_check_localizes_and_converts_in_one_pass(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify check() localizes a cross-file TypeVar and converts it to PEP 695 in the same run."""
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
        assert_that(output, not_(contains_string("T = TypeVar")))

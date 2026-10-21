# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for TypeParameterCheck.localize_imported_typevars."""

import ast
import builtins
import textwrap
from pathlib import Path
from typing import cast

import pytest
from hamcrest import all_of, assert_that, contains_string, equal_to, has_entry, has_item, has_length, not_
from pytest_mock import MockerFixture

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.recipes.type_parameter_check import TypeParameterCheck
from renaissance.recipes.type_parameter_rules import UnsafeReason


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
        expression = argument
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            expression = ast.parse(argument.value, mode="eval").body
        names.update(node.id for node in ast.walk(expression) if isinstance(node, ast.Name))
    return names - set(dir(builtins))


def _imports_after_code(module_text: str) -> list[str]:
    """Return the module-level imports of module_text that come after its first non-import statement."""
    body = ast.parse(module_text).body
    first_code = next((index for index, node in enumerate(body) if not isinstance(node, ast.Import | ast.ImportFrom)), len(body))
    return [ast.unparse(node) for node in body[first_code:] if isinstance(node, ast.Import | ast.ImportFrom)]


class TestTypeParameterCheckLocalize:
    """See module docstring."""

    def _create_cross_file(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        origin_text: str,
        importing_text: str,
        layout: tuple[str, str] = ("file_1.py", "file_2.py"),
    ) -> TypeParameterCheck:
        """Write origin_text to the origin file and return an in-memory TypeParameterCheck on the importing file holding importing_text.

        layout gives the (origin, importing) file paths, relative to tmp_path, which is the project root.
        """
        origin_rel_path, importing_rel_path = layout
        origin_file = tmp_path / origin_rel_path
        origin_file.parent.mkdir(parents=True, exist_ok=True)
        origin_file.write_text(textwrap.dedent(origin_text))

        importing_code = textwrap.dedent(importing_text)
        importing_file = str(tmp_path / importing_rel_path)
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonCstNode.load_from_text(importing_code, importing_file),
        )
        subject = TypeParameterCheck(importing_file)
        subject.in_memory = True
        subject.project_root = tmp_path
        return subject

    @pytest.mark.parametrize(
        "origin_extra",
        [
            pytest.param("def a(x: T) -> T:\n    return x", id="plain-origin"),
            pytest.param('__all__ = ["T"]', id="origin-exports-it"),
            pytest.param("class Box(Generic[T]):\n    pass", id="origin-class-is-generic-over-it"),
        ],
    )
    def test_localizes_typevar_whatever_its_origin_does_with_it(self, mocker: MockerFixture, tmp_path: Path, origin_extra: str) -> None:
        """Verify an imported TypeVar is localized, also when its origin exports it or has a class generic over it."""
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
        ("origin_ignored", "localize_imports", "localized"),
        [
            pytest.param(True, True, False, id="ignored-origin"),
            pytest.param(False, False, False, id="localization-off"),
            pytest.param(False, True, True, id="origin-not-ignored"),
        ],
    )
    def test_names_are_not_localized_from_an_ignored_origin_or_when_localization_is_off(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        *,
        origin_ignored: bool,
        localize_imports: bool,
        localized: bool,
    ) -> None:
        """Verify an import from an ignored origin, or any import with localize_imports off, is kept and recorded as ignored."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            "from typing import TypeVar\nT = TypeVar('T')\n",
            """
            from file_1 import T
            def b(x: T) -> T:
                return x
            """,
        )
        subject.localize_imports = localize_imports
        if origin_ignored:
            subject.ignore_localize_origins = frozenset({tmp_path / "file_1.py"})

        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"} if localized else {}))
        assert_that(subject.ignored_names, equal_to(set[str]() if localized else {"T"}))
        assert_that("from file_1 import T" in subject.apply_to_string(), equal_to(not localized))

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
        ("origin_imports", "expected_line"),
        [
            pytest.param("from typing import Any", "from typing import Any", id="absolute-module"),
            pytest.param("from ._shapes import Shape", "from sub._shapes import Shape", id="relative-module-in-origin"),
            pytest.param("from shapes import Base as Shape", "from shapes import Base as Shape", id="aliased-in-origin"),
        ],
    )
    def test_names_a_declaration_uses_are_imported_from_where_the_origin_gets_them(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        origin_imports: str,
        expected_line: str,
    ) -> None:
        """Verify a name the declaration uses is imported from the module the origin imports it from, not from the origin."""
        name = expected_line.rsplit(" ", maxsplit=1)[-1]
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            f'from typing import TypeVar\n{origin_imports}\nT = TypeVar("T", bound={name})\n',
            "from sub.file_1 import T\ndef b(x: T) -> T:\n    return x\n",
            ("sub/file_1.py", "use.py"),
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        lines = subject.apply_to_string().splitlines()
        assert_that(lines.count(expected_line), equal_to(1))
        assert_that(lines, not_(has_item(f"from sub.file_1 import {name}")))

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
        """Verify a declaration using a name that isn't available at module level as the same object stays imported."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            origin,
            f"from file_1 import T\n{importing_extra}\ndef biggest(items: list[T]) -> T:\n    return items[0]\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "unsafe"}))
        assert_that(subject.cross_file_unsafe_reasons, equal_to({"T": UnsafeReason.NAME_NOT_AT_MODULE_LEVEL}))
        assert_that(subject.apply_to_string(), contains_string("from file_1 import T"))

    @pytest.mark.parametrize(
        ("dunder_all", "imported_elsewhere"),
        [
            pytest.param('__all__ = ["T"]', frozenset[str](), id="re-exported-via-dunder-all"),
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
        assert_that(output, contains_string('T = TypeVar("T")'))
        assert_that(output, not_(contains_string("from file_1 import T")))

    @pytest.mark.parametrize(
        ("layout", "importing_import", "expected_line"),
        [
            pytest.param(("file_1.py", "file_2.py"), "from file_1 import T, helper", "from file_1 import helper", id="absolute"),
            pytest.param(("file_1.py", "file_2.py"), "from .file_1 import T, helper", "from .file_1 import helper", id="relative"),
            pytest.param(
                ("file_1.py", "sub/use.py"),
                "from ..file_1 import T, helper",
                "from ..file_1 import helper",
                id="relative-parent",
            ),
            pytest.param(("__init__.py", "file_2.py"), "from . import T, helper", "from . import helper", id="bare-package"),
            pytest.param(
                ("file_1.py", "file_2.py"),
                "from file_1 import T, helper as h",
                "from file_1 import helper as h",
                id="alias-kept",
            ),
        ],
    )
    def test_keeps_other_names_when_localizing_one_of_several_imports(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        layout: tuple[str, str],
        importing_import: str,
        expected_line: str,
    ) -> None:
        """Verify localizing one imported name keeps the other names imported from the same module, alias included."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            'from typing import TypeVar\nT = TypeVar("T")\ndef helper() -> None:\n    pass\n',
            f"{importing_import}\ndef b(x: T) -> T:\n    return x\n",
            layout,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        output = subject.apply_to_string()
        assert_that(output.splitlines().count(expected_line), equal_to(1))
        assert_that(output, contains_string('T = TypeVar("T")'))

    @pytest.mark.parametrize(
        ("importing_import", "comments"),
        [
            pytest.param("from file_1 import T, helper  # noqa: F401", ["# noqa: F401"], id="trailing-comment"),
            pytest.param(
                "from file_1 import (  # header\n    T,  # the typevar\n    helper,  # the helper\n)",
                ["# header", "# the helper"],
                id="multi-line",
            ),
        ],
    )
    def test_narrowing_an_import_keeps_its_comments(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        importing_import: str,
        comments: list[str],
    ) -> None:
        """Verify each comment of a narrowed import is kept once, and never on the localized declaration's line."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            'from typing import TypeVar\nT = TypeVar("T")\ndef helper() -> None:\n    pass\n',
            f"{importing_import}\ndef b(x: T) -> T:\n    helper()\n    return x\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        lines = subject.apply_to_string().splitlines()
        for comment in comments:
            holders = [line for line in lines if comment in line]
            assert_that(holders, has_length(1), comment)
            assert_that(holders[0], not_(contains_string("TypeVar(")), comment)

    @pytest.mark.parametrize(
        ("origin_extra", "importing_import", "expected_lines"),
        [
            pytest.param(
                'T = TypeVar("T")\nU = TypeVar("U")',
                "from file_1 import T, U",
                ["from typing import TypeVar", 'T = TypeVar("T")', 'U = TypeVar("U")'],
                id="two-names",
            ),
            pytest.param(
                'T = TypeVar("T")\nU = TypeVar("U")\ndef helper() -> None:\n    pass',
                "from file_1 import T, helper, U",
                ["from file_1 import helper", "from typing import TypeVar", 'T = TypeVar("T")', 'U = TypeVar("U")'],
                id="keeps-other-name",
            ),
            pytest.param(
                'class Shape:\n    pass\nclass Circle(Shape):\n    pass\nT = TypeVar("T", bound=Shape)\nU = TypeVar("U", bound=Circle)',
                "from file_1 import T, U",
                [
                    "from file_1 import Circle",
                    "from file_1 import Shape",
                    "from typing import TypeVar",
                    'T = TypeVar("T", bound=Shape)',
                    'U = TypeVar("U", bound=Circle)',
                ],
                id="bounds-each-imported-once",
            ),
        ],
    )
    def test_localizes_two_names_from_one_import_statement(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        origin_extra: str,
        importing_import: str,
        expected_lines: list[str],
    ) -> None:
        """Verify one import statement bringing in two localizable names localizes both, adding each needed import once."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            f"from typing import TypeVar\n{origin_extra}\n",
            f"{importing_import}\ndef b(x: T, y: U) -> T:\n    return x\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed", "U": "fixed"}))
        output = subject.apply_to_string()
        for line in expected_lines:
            assert_that(output.splitlines().count(line), equal_to(1), line)
        still_imported = {
            alias.name
            for node in ast.parse(output).body
            if isinstance(node, ast.ImportFrom) and node.module == "file_1"
            for alias in node.names
        }
        assert_that(still_imported & {"T", "U"}, equal_to(set()))

    @pytest.mark.parametrize(
        ("origin_import", "importing_header"),
        [
            pytest.param("from typing import TypeVar", "", id="missing-here"),
            pytest.param("from typing import TypeVar", 'from typing import TypeVar\nU = TypeVar("U")', id="already-here"),
            # The origin has no from-import of "TypeVar"; only safe because this file imports it.
            pytest.param("from typing import *", "from typing import TypeVar", id="origin-wildcard-import"),
        ],
    )
    def test_localized_file_imports_the_constructor_exactly_once(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        origin_import: str,
        importing_header: str,
    ) -> None:
        """Verify localizing adds "from typing import TypeVar" when missing and never duplicates it."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            f'{origin_import}\nT = TypeVar("T")\ndef a(x: T) -> T:\n    return x\n',
            f"{importing_header}\nfrom file_1 import T\ndef b(x: T) -> T:\n    return x\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string().count("from typing import TypeVar"), equal_to(1))

    @pytest.mark.parametrize(
        "importing_text",
        [
            pytest.param("from file_1 import T\nimport os\nfrom collections import OrderedDict\n", id="import-after-removed"),
            pytest.param("import os\nfrom file_1 import T\n", id="removed-is-last-import"),
            pytest.param("from __future__ import annotations\nfrom file_1 import T\nimport os\n", id="future-import-present"),
            pytest.param("from file_1 import T, helper\nimport os\n", id="narrowed-import"),
            pytest.param("from file_1 import T\n", id="only-import"),
        ],
    )
    def test_localized_declaration_comes_after_every_import(self, mocker: MockerFixture, tmp_path: Path, importing_text: str) -> None:
        """Verify the declaration is placed after the import block, so no import is left below code (E402)."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            'from typing import TypeVar\nT = TypeVar("T")\ndef helper() -> None:\n    pass\n',
            f"{importing_text}def b(x: T) -> T:\n    return x\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, contains_string('T = TypeVar("T")'))
        assert_that(_imports_after_code(output), equal_to([]))
        assert_that(output.count("from typing import TypeVar"), equal_to(1))

    @pytest.mark.parametrize(
        "dropped_import",
        [
            pytest.param("from file_1 import T  # noqa: F401", id="trailing-comment"),
            pytest.param("from file_1 import (\n    T,\n)  # noqa: F401", id="multi-line-trailing-comment"),
        ],
    )
    def test_dropping_an_import_drops_the_comment_on_its_line(self, mocker: MockerFixture, tmp_path: Path, dropped_import: str) -> None:
        """Verify a comment trailing a fully localized import goes with it instead of staying behind on a line of its own."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            'from typing import TypeVar\nT = TypeVar("T")\n',
            f"import os\n{dropped_import}\nimport sys\ndef b(x: T) -> T:\n    return x\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that(output, not_(contains_string("noqa")))
        assert_that(_imports_after_code(output), equal_to([]))

    @pytest.mark.parametrize(
        ("origin_extra", "expected_once"),
        [
            pytest.param('T = TypeVar("T")\nU = TypeVar("U")', ["from typing import TypeVar"], id="constructor"),
            pytest.param(
                'class Shape:\n    pass\nT = TypeVar("T", bound=Shape)\nU = TypeVar("U", bound=Shape)',
                ["from typing import TypeVar", "from file_1 import Shape"],
                id="constructor-and-bound-name",
            ),
        ],
    )
    def test_each_needed_import_is_added_once_per_file(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        origin_extra: str,
        expected_once: list[str],
    ) -> None:
        """Verify names localized from separate import statements share the imports they need, one line each per file."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            f"from typing import TypeVar\n{origin_extra}\n",
            "from file_1 import T\nfrom file_1 import U\ndef b(x: T, y: U) -> T:\n    return x\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed", "U": "fixed"}))
        output = subject.apply_to_string()
        for line in expected_once:
            assert_that(output.splitlines().count(line), equal_to(1), line)

    def test_declaration_stays_before_a_statement_that_uses_it_between_imports(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        """Verify a declaration is not moved below a module-level statement that already needs it."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            'from typing import TypeVar\nT = TypeVar("T")\n',
            "from typing import Generic\nfrom file_1 import T\nclass Box(Generic[T]):\n    pass\nimport os\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        # Running the module is what proves the declaration is bound before `Box` uses it.
        exec(compile(output, "importing.py", "exec"), {})  # noqa: S102

    @pytest.mark.parametrize(
        ("origin_declaration", "expected_comment_lines"),
        [
            pytest.param('T = TypeVar("T")  # noqa: PLC0105', ['T = TypeVar("T")  # noqa: PLC0105'], id="noqa"),
            pytest.param(
                'T = TypeVar(\n    "T",\n    bound=int,\n)  # noqa: PLC0105',
                [")  # noqa: PLC0105"],
                id="multi-line-declaration",
            ),
            pytest.param('T = TypeVar("T"); U = 1  # unrelated', [], id="shares-line-with-another-statement"),
        ],
    )
    def test_localized_declaration_keeps_the_comment_trailing_it(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        origin_declaration: str,
        expected_comment_lines: list[str],
    ) -> None:
        """Verify the comment trailing a declaration's line is copied with it, unless the line holds another statement."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            f"from typing import TypeVar\n{origin_declaration}\n",
            "from file_1 import T\ndef b(x: T) -> T:\n    return x\n",
        )
        result = subject.localize_imported_typevars()

        assert_that(result, equal_to({"T": "fixed"}))
        output = subject.apply_to_string()
        assert_that([line for line in output.splitlines() if "#" in line], equal_to(expected_comment_lines))

    @pytest.mark.parametrize(
        ("layout", "importing_header", "expected_line"),
        [
            pytest.param(("file_1.py", "file_2.py"), "from .file_1 import T", "from ._compat import TypeVar", id="same-dir"),
            pytest.param(
                ("sub/file_1.py", "use.py"),
                "from .sub.file_1 import T",
                "from .sub._compat import TypeVar",
                id="origin-in-subpackage",
            ),
            pytest.param(
                ("file_1.py", "sub/use.py"),
                "from ..file_1 import T",
                "from .._compat import TypeVar",
                id="importing-in-subpackage",
            ),
            pytest.param(("sub/file_1.py", "use.py"), "from sub.file_1 import T", "from sub._compat import TypeVar", id="absolute-via"),
            pytest.param(
                ("file_1.py", "file_2.py"),
                "from ._compat import TypeVar\nfrom .file_1 import T",
                "from ._compat import TypeVar",
                id="already-here",
            ),
            # A top-level origin's `._compat` names no package from here, so the origin itself provides TypeVar.
            pytest.param(("file_1.py", "use.py"), "from file_1 import T", "from file_1 import TypeVar", id="not-rebasable"),
        ],
    )
    def test_localized_file_imports_a_relatively_imported_constructor_from_the_same_module(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        layout: tuple[str, str],
        importing_header: str,
        expected_line: str,
    ) -> None:
        """Verify a constructor the origin imports relatively is imported once, from that same module as seen from here."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            'from ._compat import TypeVar\nT = TypeVar("T")\n',
            f"{importing_header}\ndef b(x: T) -> T:\n    return x\n",
            layout,
        )
        result = subject.localize_imported_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string().splitlines().count(expected_line), equal_to(1))

    @pytest.mark.parametrize(
        "origin_imports",
        [
            pytest.param(
                """
                import sys
                if sys.version_info >= (3, 13):
                    from typing import TypeVar
                else:
                    from typing_extensions import TypeVar
                """,
                id="python-version",
            ),
            pytest.param(
                """
                from typing import TYPE_CHECKING
                if TYPE_CHECKING:
                    from typing_extensions import TypeVar
                else:
                    from typing import TypeVar
                """,
                id="type-checking",
            ),
        ],
    )
    def test_does_not_localize_when_origin_imports_constructor_conditionally(
        self,
        mocker: MockerFixture,
        tmp_path: Path,
        origin_imports: str,
    ) -> None:
        """Verify a TypeVar whose origin imports TypeVar inside an `if` block stays imported, marked unsafe."""
        subject = self._create_cross_file(
            mocker,
            tmp_path,
            textwrap.dedent(origin_imports) + 'T = TypeVar("T", contravariant=True, default=None)\n',
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

        assert_that(excinfo.value.filename, equal_to(str(tmp_path / "file_1.py")))

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

        assert_that(result, equal_to({}))

    def test_check_localizes_then_converts(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Verify check() localizes a cross-file TypeVar, then converts it."""
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
        assert_that(
            subject.apply_to_string(),
            all_of(contains_string("def b[T](x: T) -> T:"), not_(contains_string("T = TypeVar"))),
        )

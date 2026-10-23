# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for renaissance.recipes.type_parameter_localization.plan_localizations."""

import ast
import builtins
import textwrap
from pathlib import Path
from typing import cast

import libcst as cst
import pytest
from hamcrest import assert_that, equal_to, has_entry, has_item, has_length, not_

from renaissance.recipes.type_parameter_localization import LocalizationPlan, plan_localizations
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


def _write_origin(tmp_path: Path, origin_text: str, origin_rel_path: str) -> None:
    """Write origin_text to origin_rel_path, relative to tmp_path, which is the project root."""
    origin_file = tmp_path / origin_rel_path
    origin_file.parent.mkdir(parents=True, exist_ok=True)
    origin_file.write_text(textwrap.dedent(origin_text))


def _plan(
    tmp_path: Path,
    origin_text: str,
    importing_text: str,
    layout: tuple[str, str] = ("file_1.py", "file_2.py"),
) -> LocalizationPlan:
    """Write origin_text to the origin file and return the plan for importing_text, whose file is not written.

    layout gives the (origin, importing) file paths, relative to tmp_path, which is the project root.
    """
    origin_rel_path, importing_rel_path = layout
    _write_origin(tmp_path, origin_text, origin_rel_path)
    module = cst.parse_module(textwrap.dedent(importing_text))
    return plan_localizations(module, tmp_path / importing_rel_path, tmp_path, localize_imports=True, ignore_origins=frozenset())


class TestPlanLocalizations:
    """See module docstring."""

    @pytest.mark.parametrize(
        "origin_extra",
        [
            pytest.param("def a(x: T) -> T:\n    return x", id="plain-origin"),
            pytest.param('__all__ = ["T"]', id="origin-exports-it"),
            pytest.param("class Box(Generic[T]):\n    pass", id="origin-class-is-generic-over-it"),
        ],
    )
    def test_localizes_typevar_whatever_its_origin_does_with_it(self, tmp_path: Path, origin_extra: str) -> None:
        """Verify an imported TypeVar is localized, also when its origin exports it or has a class generic over it."""
        origin = f"from typing import Generic, TypeVar\nT = TypeVar('T')\n{origin_extra}\n"
        plan = _plan(tmp_path, origin, "from file_1 import T\ndef b(x: T) -> T:\n    return x\n")

        assert_that(plan.results, equal_to({"T": "fixed"}))
        assert_that(plan.localizations, has_length(1))
        assert_that(plan.localizations[0].declarations, equal_to(["T = TypeVar('T')"]))
        assert_that(plan.localizations[0].kept, equal_to([]))

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
        tmp_path: Path,
        *,
        origin_ignored: bool,
        localize_imports: bool,
        localized: bool,
    ) -> None:
        """Verify an import from an ignored origin, or any import with localize_imports off, is kept and recorded as ignored."""
        _write_origin(tmp_path, "from typing import TypeVar\nT = TypeVar('T')\n", "file_1.py")
        plan = plan_localizations(
            cst.parse_module("from file_1 import T\ndef b(x: T) -> T:\n    return x\n"),
            tmp_path / "file_2.py",
            tmp_path,
            localize_imports=localize_imports,
            ignore_origins=frozenset({tmp_path / "file_1.py"}) if origin_ignored else frozenset(),
        )

        assert_that(plan.results, equal_to({"T": "fixed"} if localized else {}))
        assert_that(plan.ignored_names, equal_to(set[str]() if localized else {"T"}))
        assert_that(plan.localizations, has_length(1 if localized else 0))

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
    def test_localized_declaration_keeps_its_meaning(self, tmp_path: Path, declaration: str) -> None:
        """Verify the local copy has the origin's exact arguments and every name they use is defined by the imports it brings."""
        origin = f"from typing import TypeVar\nclass Shape:\n    pass\n{declaration}\n"
        plan = _plan(tmp_path, origin, "from file_1 import T\ndef biggest(items: list[T]) -> T:\n    return items[0]\n")

        assert_that(plan.results, equal_to({"T": "fixed"}))
        written = ast.parse("\n".join([*plan.localizations[0].imports, *plan.localizations[0].declarations]))
        local_call = next(node.value for node in written.body if isinstance(node, ast.Assign))
        origin_call = cast("ast.Assign", ast.parse(origin).body[-1]).value
        assert_that(ast.dump(local_call), equal_to(ast.dump(origin_call)))
        assert_that(_names_used_by(cast("ast.Call", local_call)) - _module_level_names(written), equal_to(set()))

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
        tmp_path: Path,
        origin_imports: str,
        expected_line: str,
    ) -> None:
        """Verify a name the declaration uses is imported from the module the origin imports it from, not from the origin."""
        name = expected_line.rsplit(" ", maxsplit=1)[-1]
        plan = _plan(
            tmp_path,
            f'from typing import TypeVar\n{origin_imports}\nT = TypeVar("T", bound={name})\n',
            "from sub.file_1 import T\ndef b(x: T) -> T:\n    return x\n",
            ("sub/file_1.py", "use.py"),
        )

        assert_that(plan.results, equal_to({"T": "fixed"}))
        imports = plan.localizations[0].imports
        assert_that(imports.count(expected_line), equal_to(1))
        assert_that(imports, not_(has_item(f"from sub.file_1 import {name}")))

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
        self, tmp_path: Path, origin: str, importing_extra: str
    ) -> None:
        """Verify a declaration using a name that isn't available at module level as the same object stays imported."""
        plan = _plan(
            tmp_path,
            origin,
            f"from file_1 import T\n{importing_extra}\ndef biggest(items: list[T]) -> T:\n    return items[0]\n",
        )

        assert_that(plan.results, equal_to({"T": "unsafe"}))
        assert_that(plan.unsafe_reasons, equal_to({"T": UnsafeReason.NAME_NOT_AT_MODULE_LEVEL}))
        assert_that(plan.localizations, has_length(0))

    @pytest.mark.parametrize(
        ("origin_import", "importing_header", "expected_imports"),
        [
            pytest.param("from typing import TypeVar", "", ["from typing import TypeVar"], id="missing-here"),
            pytest.param("from typing import TypeVar", 'from typing import TypeVar\nU = TypeVar("U")', [], id="already-here"),
            # The origin has no from-import of "TypeVar"; only safe because this file imports it.
            pytest.param("from typing import *", "from typing import TypeVar", [], id="origin-wildcard-import"),
        ],
    )
    def test_localized_file_imports_the_constructor_exactly_once(
        self,
        tmp_path: Path,
        origin_import: str,
        importing_header: str,
        expected_imports: list[str],
    ) -> None:
        """Verify localizing adds "from typing import TypeVar" when missing and never when the file already has it."""
        plan = _plan(
            tmp_path,
            f'{origin_import}\nT = TypeVar("T")\ndef a(x: T) -> T:\n    return x\n',
            f"{importing_header}\nfrom file_1 import T\ndef b(x: T) -> T:\n    return x\n",
        )

        assert_that(plan.results, has_entry("T", "fixed"))
        assert_that(plan.localizations[0].imports, equal_to(expected_imports))

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
        tmp_path: Path,
        origin_declaration: str,
        expected_comment_lines: list[str],
    ) -> None:
        """Verify the comment trailing a declaration's line is copied with it, unless the line holds another statement."""
        plan = _plan(
            tmp_path,
            f"from typing import TypeVar\n{origin_declaration}\n",
            "from file_1 import T\ndef b(x: T) -> T:\n    return x\n",
        )

        assert_that(plan.results, equal_to({"T": "fixed"}))
        written = "\n".join(plan.localizations[0].declarations)
        assert_that([line for line in written.splitlines() if "#" in line], equal_to(expected_comment_lines))

    @pytest.mark.parametrize(
        ("layout", "importing_header", "expected_imports"),
        [
            pytest.param(("file_1.py", "file_2.py"), "from .file_1 import T", ["from ._compat import TypeVar"], id="same-dir"),
            pytest.param(
                ("sub/file_1.py", "use.py"),
                "from .sub.file_1 import T",
                ["from .sub._compat import TypeVar"],
                id="origin-in-subpackage",
            ),
            pytest.param(
                ("file_1.py", "sub/use.py"),
                "from ..file_1 import T",
                ["from .._compat import TypeVar"],
                id="importing-in-subpackage",
            ),
            pytest.param(("sub/file_1.py", "use.py"), "from sub.file_1 import T", ["from sub._compat import TypeVar"], id="absolute-via"),
            pytest.param(
                ("file_1.py", "file_2.py"),
                "from ._compat import TypeVar\nfrom .file_1 import T",
                [],
                id="already-here",
            ),
            # A top-level origin's `._compat` names no package from here, so the origin itself provides TypeVar.
            pytest.param(("file_1.py", "use.py"), "from file_1 import T", ["from file_1 import TypeVar"], id="not-rebasable"),
        ],
    )
    def test_localized_file_imports_a_relatively_imported_constructor_from_the_same_module(
        self,
        tmp_path: Path,
        layout: tuple[str, str],
        importing_header: str,
        expected_imports: list[str],
    ) -> None:
        """Verify a constructor the origin imports relatively is imported once, from that same module as seen from here."""
        plan = _plan(
            tmp_path,
            'from ._compat import TypeVar\nT = TypeVar("T")\n',
            f"{importing_header}\ndef b(x: T) -> T:\n    return x\n",
            layout,
        )

        assert_that(plan.results, has_entry("T", "fixed"))
        assert_that(plan.localizations[0].imports, equal_to(expected_imports))

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
        tmp_path: Path,
        origin_imports: str,
    ) -> None:
        """Verify a TypeVar whose origin imports TypeVar inside an `if` block stays imported, marked unsafe."""
        plan = _plan(
            tmp_path,
            textwrap.dedent(origin_imports) + 'T = TypeVar("T", contravariant=True, default=None)\n',
            """
            from typing import TypeVar
            from file_1 import T, helper
            def b(x: T) -> None:
                helper()
            """,
        )

        assert_that(plan.results, has_entry("T", "unsafe"))
        assert_that(plan.unsafe_reasons, has_entry("T", UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY))
        assert_that(plan.localizations, has_length(0))

    def test_unparsable_origin_error_names_the_origin_file(self, tmp_path: Path) -> None:
        """Verify a syntax error in the origin module is raised with the origin file's path, not `<unknown>`."""
        with pytest.raises(SyntaxError) as excinfo:
            _plan(
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

        assert_that(excinfo.value.filename, equal_to(str(tmp_path / "file_1.py")))

    def test_no_typevar_import_found(self, tmp_path: Path) -> None:
        """Verify nothing is planned when the importing file has no cross-file TypeVar."""
        plan = _plan(
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

        assert_that(plan.results, equal_to({}))
        assert_that(plan.localizations, has_length(0))

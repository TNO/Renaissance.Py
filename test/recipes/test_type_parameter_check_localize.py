# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for how TypeParameterCheck.localize_imported_typevars writes the localizations that plan_localizations decides."""

import ast
import textwrap
from pathlib import Path

import pytest
from hamcrest import all_of, assert_that, contains_string, equal_to, has_entry, has_length, not_
from pytest_mock import MockerFixture

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.recipes.type_parameter_check import TypeParameterCheck


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

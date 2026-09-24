"""Whole-class TypeVarCheck concerns not owned by a single phase.

End-to-end check(), and the PEP 695 version gate.
"""

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest
from hamcrest import assert_that, contains_string, has_entry, is_, not_
from pytest_mock import MockerFixture

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.type_var_check import TypeVarCheck


class TestTypeVarCheck:
    """See module docstring."""

    def test_check_cleans_up_ruff_style_leftover_end_to_end(self, create_type_var_check: Callable[[str], TypeVarCheck]) -> None:
        """AI: Verify check() converts a PEP-695-ready TypeVar and leaves its ruff-style leftover for F401."""
        # "orphaned" (phase 3) stays empty here: phase 2 already drops the redundant declaration
        # once it sees the function is pre-converted.
        subject = create_type_var_check("""
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
        assert_that(output, not_(contains_string("T = TypeVar")))
        # The now-redundant `TypeVar` import itself is left for ruff's F401 to clean up - the
        # recipe only owns removing the declaration, not general unused-import detection.
        assert_that(output, contains_string("from typing import TypeVar"))

    def _create_versioned(self, mocker: MockerFixture, tmp_path: Path, min_python: tuple[int, int], code: str) -> TypeVarCheck:
        """Build an in-memory TypeVarCheck over `code` with the given min_python."""
        file_path = str(tmp_path / "subject.py")
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(textwrap.dedent(code), file_path),
        )
        subject = TypeVarCheck(file_path)
        subject.min_python = min_python
        subject.in_memory = True
        return subject

    @pytest.mark.parametrize(
        ("min_python", "expected"),
        [
            pytest.param(None, False, id="unknown"),
            pytest.param((3, 11), False, id="3.11"),
            pytest.param((3, 12), True, id="3.12"),
            pytest.param((3, 13), True, id="3.13"),
        ],
    )
    def test_pep695_gate_threshold(
        self,
        create_type_var_check: Callable[[str], TypeVarCheck],
        min_python: tuple[int, int] | None,
        *,
        expected: bool,
    ) -> None:
        """The PEP 695 gate opens only for a known min_python of 3.12 or later."""
        subject = create_type_var_check("x = 1")
        subject.min_python = min_python

        assert_that(subject._target_supports_pep695(), is_(expected))  # noqa: SLF001

    def test_convert_declared_typevars_reports_unsafe_when_target_too_old(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify convert_declared_typevars reports "unsafe" and leaves the TypeVar untouched below 3.12."""
        subject = self._create_versioned(
            mocker,
            tmp_path,
            (3, 10),
            """
            from typing import TypeVar

            def a(x: T) -> T:
                return x
            def b(y: T) -> T:
                return y

            T = TypeVar("T")
        """,
        )
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "unsafe"))
        assert_that(subject.apply_to_string(), contains_string('T = TypeVar("T")'))

    def test_convert_declared_typevars_still_fixes_when_target_new_enough(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify convert_declared_typevars still converts the TypeVar when the target is 3.12+."""
        subject = self._create_versioned(
            mocker,
            tmp_path,
            (3, 12),
            """
            from typing import TypeVar

            def a(x: T) -> T:
                return x

            T = TypeVar("T")
        """,
        )
        result = subject.convert_declared_typevars()

        assert_that(result, has_entry("T", "fixed"))
        assert_that(subject.apply_to_string(), contains_string("def a[T](x: T) -> T:"))

    def test_check_still_localizes_when_target_too_old(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """AI: Verify cross-file localization still runs when the target is too old for the PEP 695 conversion."""
        (tmp_path / "file_1.py").write_text(
            textwrap.dedent("""
            from typing import TypeVar
            T = TypeVar("T")
            def a(x: T) -> T:
                return x
            """)
        )
        importing_file = str(tmp_path / "file_2.py")
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
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
        subject.min_python = (3, 10)
        subject.in_memory = True
        subject.run()

        assert_that(subject.result["cross_file"], has_entry("T", "fixed"))
        assert_that(subject.result["converted"], has_entry("T", "unsafe"))
        output = subject.apply_to_string()
        assert_that(output, contains_string("T = TypeVar('T')"))
        assert_that(output, not_(contains_string("def b[T]")))

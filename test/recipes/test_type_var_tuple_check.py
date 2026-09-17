"""Tests for the TypeVarTupleCheck recipe."""

from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from hamcrest import assert_that, contains_inanyorder, empty, is_

from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.type_var_tuple_check import TypeVarTupleCheck, target_supports_pep646


class TestTypeVarTupleCheck:
    """See module docstring."""

    @pytest.mark.parametrize(
        "code,expected",
        [
            (
                """
            from typing import TypeVarTuple, Generic, Unpack
            Ts = TypeVarTuple("Ts")
            class Foo(Generic[Unpack[Ts]]):
                pass
            """,
                ["Ts"],
            ),
            (
                """
            from typing import TypeVarTuple
            Ts = TypeVarTuple("Ts")
            def foo(*args: *Ts) -> tuple[*Ts]:
                return args
            """,
                [],
            ),
            (
                """
            def foo(x: int) -> int:
                return x
            """,
                [],
            ),
        ],
    )
    def test_legacy_unpack_usage(
        self, make_recipe: Callable[[type[PythonRefactoring], str], PythonRefactoring], code: str, expected: list[str]
    ) -> None:
        subject = cast(TypeVarTupleCheck, make_recipe(TypeVarTupleCheck, code))
        result = subject.find_legacy_unpack_usage()
        if expected:
            assert_that(result, contains_inanyorder(*expected))
        else:
            assert_that(result, empty())

    # Deep coverage of pyproject.toml lookup/requires-python parsing lives in
    # test/utils/test_python_version.py; these two only confirm the >=(3, 11) threshold.
    def test_target_supports_pep646_true_for_3_11_plus(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
        assert_that(target_supports_pep646(str(tmp_path / "file.py")), is_(True))

    def test_target_supports_pep646_false_for_3_10(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.10"\n')
        assert_that(target_supports_pep646(str(tmp_path / "file.py")), is_(False))

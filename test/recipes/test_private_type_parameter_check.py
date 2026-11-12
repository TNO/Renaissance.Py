# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for PrivateTypeParameterCheck."""

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest
from hamcrest import assert_that, equal_to

from renaissance.recipes.private_type_parameter_check import PrivateTypeParameterCheck
from renaissance.recipes.type_parameter_rules import UnsafeReason

_PATTERN_GAP = pytest.mark.xfail(
    strict=True,
    reason="The declaration patterns cannot express default values, keyword-only or positional-only parameters.",
)


@pytest.fixture
def create_check(tmp_path: Path) -> Callable[[str], PrivateTypeParameterCheck]:
    """Build a PrivateTypeParameterCheck for dedented source text written to a file in tmp_path."""

    def _create(text: str) -> PrivateTypeParameterCheck:
        file = tmp_path / "x.py"
        file.write_text(textwrap.dedent(text), encoding="utf-8")
        subject = PrivateTypeParameterCheck(file)
        subject.in_memory = True
        return subject

    return _create


class TestPrivateTypeParameterCheck:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            pytest.param(
                """\
                def f[_T](x: _T) -> _T:
                    z: _T = x
                    return z
                """,
                """\
                def f[T](x: T) -> T:
                    z: T = x
                    return z
                """,
                id="signature_and_body",
            ),
            pytest.param(
                """\
                def f[_T, _S](x: _T, y: _S) -> _T:
                    return x
                """,
                """\
                def f[T, S](x: T, y: S) -> T:
                    return x
                """,
                id="several_parameters",
            ),
            pytest.param(
                """\
                def f[_T](x: "list[_T]") -> _T: ...
                """,
                """\
                def f[T](x: "list[T]") -> T: ...
                """,
                id="string_annotation",
            ),
            pytest.param(
                """\
                def f[_T](x: "mod._T | _T") -> _T: ...
                """,
                """\
                def f[T](x: "mod._T | T") -> T: ...
                """,
                id="attribute_with_the_same_name_in_string",
            ),
            pytest.param(
                """\
                def f[_T](x: "Annotated[_T, Field(_T=1)]") -> _T: ...
                """,
                """\
                def f[T](x: "Annotated[T, Field(_T=1)]") -> T: ...
                """,
                id="keyword_argument_with_the_same_name_in_string",
            ),
            pytest.param(
                """\
                class Box[_T]:
                    def get(self, default: _T) -> _T: ...
                """,
                """\
                class Box[T]:
                    def get(self, default: T) -> T: ...
                """,
                id="class_and_method",
            ),
            pytest.param(
                """\
                class Box[_T]:
                    def map[_U](self, f: _U) -> _U: ...
                    def get(self) -> _T: ...
                """,
                """\
                class Box[T]:
                    def map[U](self, f: U) -> U: ...
                    def get(self) -> T: ...
                """,
                id="generic_method_in_generic_class",
            ),
            pytest.param(
                """\
                @decorator
                def f[_T](x: _T): ...
                """,
                """\
                @decorator
                def f[T](x: T): ...
                """,
                id="decorated_without_return_annotation",
            ),
            pytest.param(
                """\
                def f[**_P, *_Ts](c: Callable[_P, int], *args: *_Ts) -> int: ...
                """,
                """\
                def f[**P, *Ts](c: Callable[P, int], *args: *Ts) -> int: ...
                """,
                id="param_spec_and_type_var_tuple",
            ),
            pytest.param(
                """\
                def f[_T: str = str](x: _T) -> _T: ...
                """,
                """\
                def f[T: str = str](x: T) -> T: ...
                """,
                id="bound_and_default",
            ),
            pytest.param(
                """\
                def f[_T](x: _T, *args: _T, **kwargs: _T) -> _T: ...
                """,
                """\
                def f[T](x: T, *args: T, **kwargs: T) -> T: ...
                """,
                id="variadic_and_keyword_parameters",
            ),
            pytest.param(
                """\
                def f[_T](x: _T | None = None) -> _T: ...
                """,
                """\
                def f[T](x: T | None = None) -> T: ...
                """,
                marks=_PATTERN_GAP,
                id="default_value",
            ),
            pytest.param(
                """\
                def f[_T](x, *, y: _T) -> _T: ...
                """,
                """\
                def f[T](x, *, y: T) -> T: ...
                """,
                marks=_PATTERN_GAP,
                id="keyword_only_parameter",
            ),
            pytest.param(
                """\
                def f[_T](x: _T, /) -> _T: ...
                """,
                """\
                def f[T](x: T, /) -> T: ...
                """,
                marks=_PATTERN_GAP,
                id="positional_only_parameter",
            ),
            pytest.param(
                """\
                class Box[_T](Base, metaclass=Meta):
                    a: _T
                """,
                """\
                class Box[T](Base, metaclass=Meta):
                    a: T
                """,
                id="class_with_base_and_keyword",
            ),
            pytest.param(
                """\
                from __future__ import annotations
                from typing import TypeVar

                _T = TypeVar("_T")

                def f[_T](x: _T) -> _T:
                    return x

                def g(y: _T) -> _T:
                    return y
                """,
                """\
                from __future__ import annotations
                from typing import TypeVar

                _T = TypeVar("_T")

                def f[T](x: T) -> T:
                    return x

                def g(y: _T) -> _T:
                    return y
                """,
                id="module_level_typevar_with_same_name_is_untouched",
            ),
        ],
    )
    def test_renames_private_type_parameter_and_all_its_uses(
        self, create_check: Callable[[str], PrivateTypeParameterCheck], source: str, expected: str
    ) -> None:
        """Verify a leading underscore is dropped from the type parameter and from every use it binds."""
        subject = create_check(source)
        subject.check()

        assert_that(subject.apply_to_string(), equal_to(textwrap.dedent(expected)))

    @pytest.mark.parametrize(
        ("source", "expected_reasons"),
        [
            pytest.param(
                """\
                def f[T](x: T) -> T:
                    return x
                """,
                {},
                id="public_name",
            ),
            pytest.param(
                """\
                T = 1

                def f[_T](x: _T) -> _T:
                    return T
                """,
                {"_T": UnsafeReason.NEW_NAME_NOT_FREE},
                id="outer_name_used_in_scope_would_be_captured",
            ),
            pytest.param(
                """\
                def f[_T, T](x: _T, y: T) -> _T:
                    return x
                """,
                {"_T": UnsafeReason.NEW_NAME_NOT_FREE},
                id="new_name_already_a_type_parameter",
            ),
            pytest.param(
                """\
                def f[_class](x: _class) -> _class: ...
                """,
                {"_class": UnsafeReason.NEW_NAME_NOT_FREE},
                id="new_name_is_a_keyword",
            ),
            pytest.param(
                """\
                def f[_T](x: "list[" "_T]") -> _T: ...
                """,
                {"_T": UnsafeReason.USE_NOT_RENAMEABLE},
                id="use_in_a_concatenated_string",
            ),
        ],
    )
    def test_leaves_source_unchanged_when_renaming_is_not_safe(
        self,
        create_check: Callable[[str], PrivateTypeParameterCheck],
        source: str,
        expected_reasons: dict[str, UnsafeReason],
    ) -> None:
        """Verify nothing is renamed when the name is already public or the new name would capture or clash, and why."""
        subject = create_check(source)
        result = subject.check()

        assert_that(subject.apply_to_string(), equal_to(textwrap.dedent(source)))
        assert_that(subject.unsafe_reasons, equal_to(expected_reasons))
        assert_that(result, equal_to(dict.fromkeys(expected_reasons, "unsafe")))

    @pytest.mark.parametrize(
        ("source", "expected_kinds"),
        [
            pytest.param(
                "def f[_T, **_P, *_Ts](x: _T, c: Callable[_P, int], *args: *_Ts) -> int: ...\n",
                {"_T": "TypeVar", "_P": "ParamSpec", "_Ts": "TypeVarTuple"},
                id="function",
            ),
            pytest.param("class Box[_T]:\n    a: _T\n", {"_T": "TypeVar"}, id="class"),
        ],
    )
    def test_reports_the_kind_of_each_type_parameter_it_renamed(
        self,
        create_check: Callable[[str], PrivateTypeParameterCheck],
        source: str,
        expected_kinds: dict[str, str],
    ) -> None:
        """Verify each renamed name is mapped to TypeVar, ParamSpec or TypeVarTuple."""
        subject = create_check(source)
        subject.check()

        assert_that(subject.type_param_kinds, equal_to(expected_kinds))

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for matching the PEP 695 type parameters of a function or class with `$` placeholders."""

import pytest
from hamcrest import assert_that, equal_to, has_length

from renaissance.core.match import PatternMatch, match_pattern
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode

FUNCTION_PATTERN = "def $f[$$tps]($$args) -> $r:\n    $$body"
DECORATED_FUNCTION_PATTERN = "@$$decorators\ndef $f[$$tps]($$args) -> $r:\n    $$body"
CLASS_PATTERN = "class $c[$$tps]($$bases):\n    $$body"


def _find(pattern: str, code: str) -> list[PatternMatch]:
    """Return the matches of pattern in code, parsed with the RST backend."""
    factory = PythonFactory(PythonRstNode)
    root = factory.create_from_text(code, "demo.py")
    return list(match_pattern([root], PythonPatternFactory(factory).create_statements(pattern)))


class TestPatternTypeParameters:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("pattern", "code", "expected_count"),
        [
            pytest.param(FUNCTION_PATTERN, "def f[_T](x: _T) -> _T:\n    return x\n", 1, id="function_one"),
            pytest.param(FUNCTION_PATTERN, "def f[A, B](a: A, b: B) -> A:\n    return a\n", 2, id="function_two"),
            pytest.param(FUNCTION_PATTERN, "def f[A, B, C](a: A) -> A:\n    return a\n", 3, id="function_three"),
            pytest.param(FUNCTION_PATTERN, "def f[_T: int](x: _T) -> _T:\n    return x\n", 1, id="function_bound"),
            pytest.param(FUNCTION_PATTERN, "def f[**_P](x) -> int:\n    return 1\n", 1, id="function_param_spec"),
            pytest.param(FUNCTION_PATTERN, "def f[*_Ts](x) -> int:\n    return 1\n", 1, id="function_type_var_tuple"),
            pytest.param(FUNCTION_PATTERN, "async def f[A, B](a: A) -> B:\n    return a\n", 2, id="async_function"),
            pytest.param(DECORATED_FUNCTION_PATTERN, "@d\ndef f[A, B](a: A) -> B:\n    return a\n", 2, id="decorated_function"),
            pytest.param(CLASS_PATTERN, "class C[_T]:\n    a: _T\n", 1, id="class_one"),
            pytest.param(CLASS_PATTERN, "class C[A, B]:\n    a: A\n", 2, id="class_two"),
            pytest.param(CLASS_PATTERN, "class C[A, B](Base):\n    a: A\n", 2, id="class_with_base"),
        ],
    )
    def test_placeholder_captures_every_type_parameter(self, pattern: str, code: str, expected_count: int) -> None:
        """Verify `[$$tps]` matches the declaration and captures all of its type parameters, whatever their number or kind."""
        matches = _find(pattern, code)

        assert_that(matches, has_length(1))
        assert_that(matches[0].expansions["$$tps"], has_length(expected_count))

    def test_single_placeholder_captures_a_node(self) -> None:
        """Verify `[$t]` captures the type parameter as a node with its position, not as its name text."""
        matches = _find("def $f[$t]($$args) -> $r:\n    $$body", "def f[_T](x: _T) -> _T:\n    return x\n")

        assert_that(matches, has_length(1))
        captured = matches[0].expansions["$t"][0]
        assert_that(type(captured), equal_to(PythonRstNode))
        assert_that(captured.signature, equal_to("_T"))

    @pytest.mark.parametrize(
        ("code", "expected_count"),
        [
            pytest.param("def f[T](x: T) -> T:\n    return x\n", 1, id="same_name"),
            pytest.param("def f[_T](x: _T) -> _T:\n    return x\n", 0, id="other_name"),
        ],
    )
    def test_written_type_parameter_matches_only_that_name(self, code: str, expected_count: int) -> None:
        """Verify a type parameter written in the pattern matches the same name only."""
        matches = _find("def $f[T]($$args) -> $r:\n    $$body", code)

        assert_that(matches, has_length(expected_count))

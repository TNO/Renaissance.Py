# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for matching the keyword arguments of a class or a call with the `**$$kws` placeholder."""

import pytest
from hamcrest import assert_that, equal_to, has_length

from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree.match_finder import PatternMatch, match_pattern

CLASS_PATTERN = "class $c($$bases, **$$kws):\n    $$body"
DECORATED_CLASS_PATTERN = "@$$decorators\nclass $c[$$tps]($$bases, **$$kws):\n    $$body"
CALL_PATTERN = "f($$args, **$$kws)"


def _find(pattern: str, code: str) -> list[PatternMatch]:
    """Return the matches of pattern in code, parsed with the RST backend."""
    factory = PythonFactory(PythonRstNode)
    root = factory.create_from_text(code, "demo.py")
    return list(match_pattern([root], PythonPatternFactory(factory).create_statements(pattern)))


class TestPatternKeywords:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("pattern", "code", "expected_keywords"),
        [
            pytest.param(CLASS_PATTERN, "class C:\n    pass\n", [], id="class_without_bases"),
            pytest.param(CLASS_PATTERN, "class C(B):\n    pass\n", [], id="class_without_keywords"),
            pytest.param(CLASS_PATTERN, "class C(B, metaclass=M):\n    pass\n", ["metaclass=M"], id="class_one_keyword"),
            pytest.param(CLASS_PATTERN, "class C(metaclass=M):\n    pass\n", ["metaclass=M"], id="class_only_keyword"),
            pytest.param(
                CLASS_PATTERN,
                "class C(B, metaclass=M, flag=True):\n    pass\n",
                ["metaclass=M", "flag=True"],
                id="class_several_keywords",
            ),
            pytest.param(CLASS_PATTERN, "class C(B, **options):\n    pass\n", ["**options"], id="class_unpacked_keywords"),
            pytest.param(
                DECORATED_CLASS_PATTERN,
                "@d\nclass C[T](B, x=1, **options):\n    pass\n",
                ["x=1", "**options"],
                id="decorated_generic_class",
            ),
            pytest.param(CALL_PATTERN, "f()\n", [], id="call_without_arguments"),
            pytest.param(CALL_PATTERN, "f(1)\n", [], id="call_without_keywords"),
            pytest.param(CALL_PATTERN, "f(1, a=2, b=3)\n", ["a=2", "b=3"], id="call_several_keywords"),
            pytest.param(CALL_PATTERN, "f(**options)\n", ["**options"], id="call_unpacked_keywords"),
        ],
    )
    def test_placeholder_captures_every_keyword_argument(self, pattern: str, code: str, expected_keywords: list[str]) -> None:
        """Verify `**$$kws` matches the class or call whatever its number of keyword arguments and captures each one."""
        matches = _find(pattern, code)

        assert_that(matches, has_length(1))
        assert_that([keyword.signature for keyword in matches[0].expansions["$$kws"]], equal_to(expected_keywords))

    def test_written_base_class_must_be_the_same(self) -> None:
        """Verify a base class written in the pattern, as in `class $c(Base, **$$kws)`, matches only that base."""
        pattern = "class $c(Base, **$$kws):\n    $$body"

        assert_that(_find(pattern, "class C(Base, metaclass=M):\n    pass\n"), has_length(1))
        assert_that(_find(pattern, "class C(Other, metaclass=M):\n    pass\n"), has_length(0))

    def test_named_keyword_placeholder_still_captures_its_name_and_value(self) -> None:
        """Verify `$kw=$v` keeps matching one keyword argument and binding its name and value."""
        matches = _find("class $c($$bases, $kw=$v):\n    $$body", "class C(B, metaclass=M):\n    pass\n")

        assert_that(matches, has_length(1))
        assert_that(matches[0].expansions["$kw"], equal_to(["metaclass"]))
        assert_that(matches[0].expansions["$v"][0].signature, equal_to("M"))

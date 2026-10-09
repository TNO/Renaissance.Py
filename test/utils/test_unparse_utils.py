"""Tests for the signature-only PEP 695 bracket-splice helpers."""

import ast
import textwrap
from typing import cast

import pytest
from hamcrest import assert_that, equal_to

from renaissance.utils.unparse_utils import (
    _bracket_end_offset,  # pyright: ignore[reportPrivateUsage]
    _header_end_line,  # pyright: ignore[reportPrivateUsage]
    _name_end_offset,  # pyright: ignore[reportPrivateUsage]
    unparse_signature_only,
)


class TestNameEndOffset:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("source", "name", "expected"),
        [
            pytest.param("def f(x: int) -> int:\n    return x\n", "f", 5, id="plain-def"),
            pytest.param("async def g(x: int) -> int:\n    return x\n", "g", 11, id="async-def"),
            pytest.param("@overload\n    def __call__(self, x: int) -> int: ...\n", "__call__", 26, id="indented-after-decorator"),
        ],
    )
    def test_finds_the_offset_after_the_name(self, source: str, name: str, expected: int) -> None:
        """Verify the offset right after the function name in its "def" line."""
        assert_that(_name_end_offset(source, name), equal_to(expected))

    def test_raises_when_name_not_found(self) -> None:
        """Verify a ValueError is raised when the function name doesn't appear in the source."""
        with pytest.raises(ValueError, match="no 'def f' header found"):
            _name_end_offset("x = 1\n", "f")


class TestBracketEndOffset:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            pytest.param("def f[T](x: T) -> T:\n    return x\n", 8, id="simple"),
            pytest.param("def f[T: list[int]](x: T) -> T:\n    return x\n", 19, id="nested-bracket-in-bound"),
        ],
    )
    def test_finds_the_matching_closing_bracket(self, source: str, expected: int) -> None:
        """Verify the offset right after the "]" matching the type-param bracket, across nested brackets."""
        assert_that(_bracket_end_offset(source, 5), equal_to(expected))


class TestHeaderEndLine:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            pytest.param("def f(x: int) -> int:\n    return x\n", 1, id="one-line-signature"),
            pytest.param("def f(\n    a: int,\n    b: str,\n) -> None:\n    pass\n", 4, id="multi-line-signature"),
            pytest.param('def f(\n    b: str = "x:y",\n) -> None:\n    pass\n', 3, id="colon-in-string-default"),
            pytest.param("def f(cb=lambda: 1) -> int:\n    return cb()\n", 1, id="colon-in-lambda-default"),
        ],
    )
    def test_finds_the_line_of_the_header_terminating_colon(self, source: str, expected: int) -> None:
        """Verify the header ends on the line of its own ":", not one inside a default value."""
        assert_that(_header_end_line(source), equal_to(expected))

    def test_raises_when_no_header_terminating_colon(self) -> None:
        """Verify a ValueError is raised when the source has no header-terminating colon at all."""
        with pytest.raises(ValueError, match="no header-terminating ':' found"):
            _header_end_line("x = 1\n")


class TestUnparseSignatureOnly:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("original", "expected"),
        [
            pytest.param(
                textwrap.dedent("""\
                    def f(x):
                        # explains something
                        return x
                """),
                "def f[T](x):\n    # explains something\n    return x\n",
                id="body-comment",
            ),
            # 8 spaces: one level for the class, one for the method body.
            pytest.param("def f(x):\n        return x", "def f[T](x):\n    return x", id="method-body-absolute-indent"),
            pytest.param("def f(x): ...\n", "def f[T](x): ...\n", id="inline-body"),
            pytest.param(
                "def f(\n    x: int,\n    y: int = 1,\n) -> int:\n    return x\n",
                "def f[T](\n    x: int,\n    y: int = 1,\n) -> int:\n    return x\n",
                id="multi-line-signature",
            ),
            pytest.param("def f[U](x: U, y):\n    return x\n", "def f[U, T](x: U, y):\n    return x\n", id="existing-bracket"),
        ],
    )
    def test_adds_the_bracket_and_keeps_everything_else(self, original: str, expected: str) -> None:
        """Verify adding T inserts or extends the type-param bracket and keeps the rest of the source."""
        node = cast("ast.FunctionDef", ast.parse(original).body[0])
        node.type_params = [*node.type_params, ast.TypeVar(name="T")]

        assert_that(unparse_signature_only(node, original), equal_to(expected))

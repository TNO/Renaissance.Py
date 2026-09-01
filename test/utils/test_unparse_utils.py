"""Tests for the signature-only PEP 695 bracket-splice helpers."""

import ast
import textwrap

from hamcrest import assert_that, contains_string, is_

from renaissance.utils.unparse_utils import (
    _bracket_end_offset,
    _header_end_line,
    _name_end_offset,
    _type_params_bracket,
    unparse_signature_only,
)


class TestNameEndOffset:
    """See module docstring."""

    def test_finds_a_plain_def(self) -> None:
        assert_that(_name_end_offset("def f(x: int) -> int:\n    return x\n", "f"), is_(5))

    def test_finds_an_async_def(self) -> None:
        source = "async def g(x: int) -> int:\n    return x\n"
        assert_that(_name_end_offset(source, "g"), is_(11))

    def test_finds_a_def_indented_after_a_decorator(self) -> None:
        # A decorated method's .text includes the decorator on line 1 - the "def" line itself
        # is a continuation line carrying its own real indentation, not flush at column 0.
        source = "@overload\n    def __call__(self, x: int) -> int: ...\n"
        assert_that(_name_end_offset(source, "__call__"), is_(26))

    def test_raises_when_name_not_found(self) -> None:
        try:
            _name_end_offset("x = 1\n", "f")
        except ValueError:
            return
        raise AssertionError("expected ValueError")


class TestBracketEndOffset:
    """See module docstring."""

    def test_finds_a_simple_bracket(self) -> None:
        source = "def f[T](x: T) -> T:\n    return x\n"
        assert_that(_bracket_end_offset(source, 5), is_(8))

    def test_tracks_a_nested_bracket_in_a_bound(self) -> None:
        source = "def f[T: list[int]](x: T) -> T:\n    return x\n"
        assert_that(_bracket_end_offset(source, 5), is_(19))


class TestTypeParamsBracket:
    """See module docstring."""

    def test_no_type_params_returns_empty(self) -> None:
        node = ast.parse("def f(x): pass").body[0]
        assert_that(_type_params_bracket(node), is_(""))

    def test_one_type_param(self) -> None:
        node = ast.parse("def f(x): pass").body[0]
        node.type_params = [ast.TypeVar(name="T")]
        assert_that(_type_params_bracket(node), is_("[T]"))

    def test_two_type_params(self) -> None:
        node = ast.parse("def f(x): pass").body[0]
        node.type_params = [ast.TypeVar(name="U"), ast.TypeVar(name="T")]
        assert_that(_type_params_bracket(node), is_("[U, T]"))


class TestHeaderEndLine:
    """See module docstring."""

    def test_one_line_signature(self) -> None:
        assert_that(_header_end_line("def f(x: int) -> int:\n    return x\n"), is_(1))

    def test_multi_line_signature(self) -> None:
        source = "def f(\n    a: int,\n    b: str,\n) -> None:\n    pass\n"
        assert_that(_header_end_line(source), is_(4))

    def test_ignores_colon_inside_a_string_default(self) -> None:
        source = 'def f(\n    b: str = "x:y",\n) -> None:\n    pass\n'
        assert_that(_header_end_line(source), is_(3))

    def test_ignores_colon_inside_a_lambda_default(self) -> None:
        source = "def f(cb=lambda: 1) -> int:\n    return cb()\n"
        assert_that(_header_end_line(source), is_(1))

    def test_raises_when_no_header_terminating_colon(self) -> None:
        try:
            _header_end_line("x = 1\n")
        except ValueError:
            return
        raise AssertionError("expected ValueError")


class TestUnparseSignatureOnly:
    """See module docstring."""

    def test_preserves_a_body_comment(self) -> None:
        original = textwrap.dedent("""\
            def f(x):
                # explains something
                return x
        """)
        node = ast.parse(original).body[0]
        node.type_params = [ast.TypeVar(name="T")]

        result = unparse_signature_only(node, original)

        assert_that(result, contains_string("def f[T](x):"))
        assert_that(result, contains_string("# explains something"))

    def test_renormalizes_a_method_bodys_absolute_indent_to_four_spaces(self) -> None:
        # A method's .text carries the file's real (absolute) indentation - here 8 spaces, one
        # level of class plus one level of method body - not the 4-space-relative-to-zero
        # baseline the rewrite pipeline's shift expects.
        original = "def f(x):\n        return x"
        node = ast.parse(original).body[0]
        node.type_params = [ast.TypeVar(name="T")]

        result = unparse_signature_only(node, original)

        assert_that(result, is_("def f[T](x):\n    return x"))

    def test_preserves_an_inline_single_line_body(self) -> None:
        # "def f(x): ..." keeps its body on the header's own line - there's no separate block
        # to renormalize, and the original inline style should survive as-is.
        original = "def f(x): ...\n"
        node = ast.parse(original).body[0]
        node.type_params = [ast.TypeVar(name="T")]

        result = unparse_signature_only(node, original)

        assert_that(result, is_("def f[T](x): ...\n"))

    def test_preserves_a_multiline_signature(self) -> None:
        # Regression test: unparse_signature_only used to regenerate the whole header via
        # ast.unparse(), collapsing a multi-line parameter list onto one line.
        original = "def f(\n    x: int,\n    y: int = 1,\n) -> int:\n    return x\n"
        node = ast.parse(original).body[0]
        node.type_params = [ast.TypeVar(name="T")]

        result = unparse_signature_only(node, original)

        assert_that(result, is_("def f[T](\n    x: int,\n    y: int = 1,\n) -> int:\n    return x\n"))

    def test_merges_into_an_existing_bracket(self) -> None:
        original = "def f[U](x: U, y):\n    return x\n"
        node = ast.parse(original).body[0]
        node.type_params = [*node.type_params, ast.TypeVar(name="T")]

        result = unparse_signature_only(node, original)

        assert_that(result, is_("def f[U, T](x: U, y):\n    return x\n"))

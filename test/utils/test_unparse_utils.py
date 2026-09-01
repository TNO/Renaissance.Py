"""Tests for the signature-only ast.unparse() replacement helpers."""

import ast
import textwrap

from hamcrest import assert_that, contains_string, is_

from renaissance.utils.unparse_utils import _header_end_position, unparse_signature_only


class TestHeaderEndPosition:
    """See module docstring."""

    def test_one_line_signature(self) -> None:
        assert_that(_header_end_position("def f(x: int) -> int:\n    return x\n"), is_((1, 21)))

    def test_multi_line_signature(self) -> None:
        source = "def f(\n    a: int,\n    b: str,\n) -> None:\n    pass\n"
        assert_that(_header_end_position(source), is_((4, 10)))

    def test_ignores_colon_inside_a_string_default(self) -> None:
        source = 'def f(\n    b: str = "x:y",\n) -> None:\n    pass\n'
        assert_that(_header_end_position(source), is_((3, 10)))

    def test_ignores_colon_inside_a_lambda_default(self) -> None:
        source = "def f(cb=lambda: 1) -> int:\n    return cb()\n"
        assert_that(_header_end_position(source), is_((1, 27)))

    def test_ignores_decorator_line_when_start_line_given(self) -> None:
        source = "@decorator\nasync def g(x: int) -> int:\n    return x\n"
        assert_that(_header_end_position(source, start_line=2), is_((2, 27)))

    def test_raises_when_no_header_terminating_colon(self) -> None:
        try:
            _header_end_position("x = 1\n")
        except ValueError:
            return
        raise AssertionError("expected ValueError")


class TestUnparseSignatureOnly:
    """See module docstring."""

    def test_preserves_a_body_comment(self) -> None:
        original = textwrap.dedent('''\
            def f(x):
                # explains something
                return x
        ''')
        node = ast.parse(original).body[0]
        node.type_params = [ast.TypeVar(name="T")]

        result = unparse_signature_only(node, original)

        assert_that(result, contains_string("def f[T](x):"))
        assert_that(result, contains_string("# explains something"))

    def test_renormalizes_a_method_bodys_absolute_indent_to_four_spaces(self) -> None:
        # A method's .text carries the file's real (absolute) indentation - here 8 spaces, one
        # level of class plus one level of method body - not the 4-space-relative-to-zero
        # baseline ast.unparse() and the rewrite pipeline's shift both expect.
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

        assert_that(result, is_("def f[T](x): ..."))

"""Tests that Python node offsets address the same units as the byte-oriented rewriter.

`_RewriteActions` slices `node.text.encode(...)`, so every backend's `offset`/`end_offset`
must be expressed in UTF-8 bytes. These tests pin which backends honour that and which do not.
"""

import sys
from collections.abc import Callable
from typing import cast

import pytest
from hamcrest import assert_that, greater_than, is_

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.integrations.python.ast.factory import PythonFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.integrations.tree_sitter.lst import LSTNode
from renaissance.syntax_tree.ast_rewriter import ASTRewriter, Rewritable

type PythonNode = PythonRstNode | PythonCstNode | LSTNode

ASCII_SOURCE = 'x = "abc"\ny = f(1)\n'
# Each 'e-acute' is one character but two UTF-8 bytes, so character and byte offsets diverge after it.
NON_ASCII_SOURCE = 'x = "\u00e9\u00e9\u00e9"\ny = f(1)\n'

LST_ENCODING_REASON = (
    "LSTNode.offset is a byte offset from tree-sitter, but length is len(signature) in characters "
    "and the signature itself is cut out of the source with byte offsets applied to str, so both "
    "the span and the text slip by one per extra UTF-8 byte."
)


def _rst_root(source: str) -> PythonRstNode:
    return PythonRstNode.load_from_text(source, "offsets.py")


def _cst_root(source: str) -> PythonCstNode:
    return PythonCstNode.load_from_text(source, "offsets.py")


def _lst_root(source: str) -> LSTNode:
    return cast("LSTNode", PythonFactory(LSTNode).create_from_text(source, "offsets.py"))


def _rewriter_slice(root: Rewritable, node: Rewritable) -> bytes:
    """Cut node out of root the way _RewriteActions does, exposing any offset-unit mismatch."""
    content = root.text.encode(sys.getfilesystemencoding())
    return content[node.offset - root.offset : node.end_offset - root.offset]


def _assert_first_statement_is_addressable(root: PythonNode) -> None:
    statement = cast("Rewritable", root.children[0])
    expected = statement.text.encode(sys.getfilesystemencoding())

    assert_that(_rewriter_slice(root, statement).strip(), is_(expected.strip()))


@pytest.mark.parametrize(
    "load",
    [
        pytest.param(_rst_root, id="rst"),
        pytest.param(_cst_root, id="cst"),
        pytest.param(_lst_root, id="lst"),
    ],
)
def test_offsets_address_bytes_for_ascii_source(load: Callable[[str], PythonNode]) -> None:
    """AI: Assert every backend agrees with the rewriter while characters and bytes still coincide."""
    _assert_first_statement_is_addressable(load(ASCII_SOURCE))


@pytest.mark.parametrize(
    "load",
    [
        pytest.param(_rst_root, id="rst"),
        pytest.param(_cst_root, id="cst"),
        pytest.param(_lst_root, id="lst", marks=pytest.mark.xfail(reason=LST_ENCODING_REASON, strict=True)),
    ],
)
def test_offsets_address_bytes_for_non_ascii_source(load: Callable[[str], PythonNode]) -> None:
    """AI: Assert the rewriter's byte slice still matches the node's own text once the source holds non-ASCII."""
    _assert_first_statement_is_addressable(load(NON_ASCII_SOURCE))


@pytest.mark.parametrize(
    "load",
    [
        pytest.param(_rst_root, id="rst"),
        pytest.param(_cst_root, id="cst"),
        pytest.param(_lst_root, id="lst"),
    ],
)
def test_trailing_statement_ends_after_it_starts(load: Callable[[str], PythonNode]) -> None:
    """AI: Assert the last top-level statement reports a usable span, independently of any encoding concern."""
    trailing = load(ASCII_SOURCE).children[-1]

    assert_that(trailing.end_offset, is_(greater_than(trailing.offset)))


@pytest.mark.parametrize(
    "load",
    [
        pytest.param(_rst_root, id="rst"),
        pytest.param(_cst_root, id="cst"),
        pytest.param(_lst_root, id="lst", marks=pytest.mark.xfail(reason=LST_ENCODING_REASON, strict=True)),
    ],
)
def test_rewrite_preserves_non_ascii_text_outside_the_replaced_node(load: Callable[[str], PythonNode]) -> None:
    """AI: Assert replacing the last statement leaves the preceding non-ASCII line intact."""
    root = load(NON_ASCII_SOURCE)
    rewriter = ASTRewriter(root)
    rewriter.replace("y = g(2)", root.children[-1])

    assert_that(rewriter.apply_to_string(), is_('x = "\u00e9\u00e9\u00e9"\ny = g(2)\n'))

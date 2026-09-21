"""Tests for the Pythonic RST AST node wrapper."""

import ast

from hamcrest import assert_that, is_, not_none

from renaissance.integrations.python.ast.rst_node import PythonRstNode


class TestPythonicNode:
    """AI: Tests for the Pythonic RST AST node wrapper."""

    def test_it_can_be_created(self):
        """AI: Verify a PythonRstNode can be created from a bare ast.Pass node."""
        it = PythonRstNode(ast.Pass())
        assert_that(it, is_(not_none()))

    def test_it_has_elements(self):
        """AI: Verify indexing a PythonRstNode returns the same element as its children property."""
        it = PythonRstNode(ast.parse("def fun():  pass"))
        assert_that(it[0], is_(it.children[0]))

    def test_it_has_multiple_elements(self):
        """AI: Verify slicing a PythonRstNode returns the same slice as its children property."""
        it = PythonRstNode(ast.parse("def fun():  pass"))
        it = PythonRstNode(ast.parse("0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n"))
        assert_that(it[1:3], is_(it.children[1:3]))

"""Tests for creating C/C++ AST nodes via ASTFactory."""

import pytest
from hamcrest import assert_that, is_, not_none

from renaissance.syntax_tree import ASTShower

from .factories import Factories


class TestASTFactory:
    """AI: Tests creating C/C++ AST nodes via ASTFactory."""

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_create(self, _, factory):
        """AI: Verify factory.create_from_text parses C source and produces a renderable AST node."""
        ast = factory.create_from_text("/*comment1 */ int main()  { return 0; } /* comment at end */", "test.c")
        text = ASTShower.get_node(ast)
        assert_that(text, is_(not_none()))

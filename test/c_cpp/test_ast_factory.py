import pytest
from hamcrest import assert_that, is_, not_none

from renaissance.syntax_tree import ASTShower

from .factories import Factories


class TestASTFactory:
    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_create(self, _, factory):
        ast = factory.create_from_text("/*comment1 */ int main()  { return 0; } /* comment at end */", "test.c")
        text = ASTShower.get_node(ast)
        assert_that(text, is_(not_none()))

from unittest import TestCase
from syntax_tree import ASTShower
from .factories import Factories
from parameterized import parameterized

class TestASTFactory(TestCase):

    @parameterized.expand(Factories.factories)
    def test_create(self, _, factory):
        ast =  factory.create_from_text('/*comment1 */ int main()  { return 0; } /* comment at end */', "test.c")
        ASTShower.show_node(ast)


from unittest import TestCase
from parameterized import parameterized
from syntax_tree import ASTShower
from .factories import Factories

class TestASTFactory(TestCase):

    @parameterized.expand(Factories.factories)
    def test_create(self, _, factory):
        ast =  factory.create_from_text('/*comment1 */ int main()  { return 0; } /* comment at end */', "test.c")
        ASTShower.show_node(ast)


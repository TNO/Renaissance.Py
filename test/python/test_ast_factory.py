import unittest
from parameterized import parameterized
from renaissance.syntax_tree import ASTShower
from .factories import Factories

class TestASTFactory(unittest.TestCase):

    @parameterized.expand(Factories.factories)
    def test_create(self, _, factory):
        python_code = '# comment1\ndef main():\n    return 0\n# comment at end\nif __name__ == "__main__":\n    main()'
        python_code2 = 'class A:\n    def __init__(self, x):\n        self.x = x\n\ndef f():\n    a = A(3)'
        ast =  factory.create_from_text(python_code2, "test.py")
        ASTShower.show_node(ast)


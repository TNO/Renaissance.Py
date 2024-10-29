from unittest import TestCase

from parameterized import parameterized
from syntax_tree import ASTFinder, ASTNode

from test.c_cpp.factories import Factories
from test.clang.test_model_loader import TestModelLoader

class TestFinder(TestCase):
    pass

class TestKindFinder(TestFinder):

    @parameterized.expand(Factories.factories)
    def test_find_bogus(self, _, factory):
        model = TestModelLoader.load_model(factory)
        iter = ASTFinder.find_kind(model, '(?i).*bogus.*')
        total = len(list(iter))
        self.assertEqual( total, 0)
        print( total)

    @parameterized.expand(Factories.factories)
    def test_find_expr(self, _, factory):
        model = TestModelLoader.load_model(factory)
        iter = ASTFinder.find_kind(model, '(?i).*expr.*')
        total = len(list(iter))
        self.assertGreater( total, 0)
        print( total)

class TestAllFinder(TestFinder):

    @parameterized.expand(Factories.factories)
    def test_find_all_bogus(self, _, factory):
        model = TestModelLoader.load_model(factory)
        def isBogus(node: ASTNode):
            if 'Bogus' in node.get_kind(): yield node
        iter = ASTFinder.find_all(model, isBogus)
        total = len(list(iter))
        self.assertEqual( total, 0)
        print( total)

    @parameterized.expand(Factories.factories)
    def test_find_all_expr(self, _, factory):
        model = TestModelLoader.load_model(factory)
        def isBinaryOperator(node: ASTNode):
            if 'BINARY_OPERATOR' in node.get_kind(): yield node
        iter = ASTFinder.find_all(model, isBinaryOperator)
        total = len(list(iter))
        self.assertGreater( total, 0)
        print( total)

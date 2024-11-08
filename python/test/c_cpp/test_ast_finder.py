import re
from unittest import TestCase

from parameterized import parameterized
from syntax_tree import ASTFinder, ASTNode

from .factories import Factories
from test.syntax_tree.model_loader import ModelLoader

class TestFinder(TestCase):
    pass

class TestKindFinder(TestFinder):

    @parameterized.expand(Factories.factories)
    def test_find_bogus(self, _, factory):
        model = ModelLoader.load_model(factory)
        total = ASTFinder.find_kind(model, '(?i).*bogus.*').count()
        self.assertEqual( total, 0)
        print( total)

    @parameterized.expand(Factories.factories)
    def test_find_expr(self, _, factory):
        model = ModelLoader.load_model(factory)
        total = ASTFinder.find_kind(model, '(?i).*expr.*').count()
        self.assertGreater( total, 0)
        print( total)

class TestAllFinder(TestFinder):

    @parameterized.expand(Factories.factories)
    def test_find_all_bogus(self, _, factory):
        model = ModelLoader.load_model(factory)
        def isBogus(node: ASTNode):
            if 'Bogus' in node.get_kind(): yield node
        total = ASTFinder.find_all(model, isBogus).count()
        self.assertEqual( total, 0)
        print( total)

    @parameterized.expand(Factories.factories)
    def test_find_all_expr(self, _, factory):
        model = ModelLoader.load_model(factory)
        def isBinaryOperator(node: ASTNode):
            if re.fullmatch('(?i).*binary_?operator',node.get_kind()) : yield node
        total = ASTFinder.find_all(model, isBinaryOperator).count()
        self.assertGreater( total, 0)
        print( total)

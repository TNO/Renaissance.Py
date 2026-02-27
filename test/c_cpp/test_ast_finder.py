import re
import unittest
from pathlib import Path
from unittest import TestCase

from parameterized import parameterized
from renaissance.syntax_tree import ASTFinder, ASTNode, ASTFactory

from .factories import Factories


class ModelLoader:

    @staticmethod
    def load_model(factory: ASTFactory):
        # note: make sure to load a corresponding model for the language
        return factory.create(Path(__file__).parents[3] / 'features' / 'targets' / 'main.c')


class TestFinder(TestCase):
    pass


class TestKindFinder(TestFinder):

    @parameterized.expand(Factories.factories)
    @unittest.skip("This test is currently not working")
    def test_find_bogus(self, _, factory):
        model = ModelLoader.load_model(factory)
        total = ASTFinder.find_kind(model, '(?i).*bogus.*').count()
        self.assertEqual(total, 0)
        print(total)

    @parameterized.expand(Factories.factories)
    @unittest.skip("This test is currently not working")
    def test_find_expr(self, _, factory):
        model = ModelLoader.load_model(factory)
        total = ASTFinder.find_kind(model, '(?i).*expr.*').count()
        self.assertGreater(total, 0)
        print(total)


class TestAllFinder(TestFinder):

    @parameterized.expand(Factories.factories)
    @unittest.skip("This test is currently not working")
    def test_find_all_bogus(self, _, factory):
        model = ModelLoader.load_model(factory)

        def isBogus(node: ASTNode):
            if 'Bogus' in node.kind: yield node

        total = ASTFinder.find_all(model, isBogus).count()
        self.assertEqual(total, 0)
        print(total)

    @parameterized.expand(Factories.factories)
    @unittest.skip("This test is currently not working")
    def test_find_all_expr(self, _, factory):
        model = ModelLoader.load_model(factory)

        def isBinaryOperator(node: ASTNode):
            if re.fullmatch('(?i).*binary_?operator', node.kind): yield node

        total = ASTFinder.find_all(model, isBinaryOperator).count()
        self.assertGreater(total, 0)
        print(total)

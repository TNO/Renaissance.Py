import re
from pathlib import Path
from unittest import TestCase

from hamcrest import assert_that, is_, greater_than
from parameterized import parameterized

from renaissance.syntax_tree import ASTFinder, ASTNode, ASTFactory, ASTShower
from .factories import Factories


class ModelLoader:

    @staticmethod
    def load_model(factory: ASTFactory):
        # note: make sure to load a corresponding model for the language
        return factory.create(Path('../features/targets/main.c'))


class TestFinder(TestCase):
    pass


class TestKindFinder(TestFinder):

    @parameterized.expand(Factories.factories)
    def test_find_bogus(self, _, factory):
        model = ModelLoader.load_model(factory)
        total = ASTFinder.find_kind(model, '(?i).*bogus.*').count()
        assert_that(total, is_(0))

    @parameterized.expand(Factories.factories)
    def test_find_expr(self, _, factory):
        model = ModelLoader.load_model(factory)
        ASTShower.show_node(model)
        total = ASTFinder.find_kind(model, '(?i).*expr.*').count()
        assert_that(total, greater_than(0))


class TestAllFinder(TestFinder):

    @parameterized.expand(Factories.factories)
    def test_find_all_bogus(self, _, factory):
        model = ModelLoader.load_model(factory)

        def is_bogus(node: ASTNode):
            if 'Bogus' in node.kind: yield node

        total = ASTFinder.find_all(model, is_bogus).count()
        assert_that(total, is_(0))

    @parameterized.expand(Factories.factories)
    def test_find_all_expr(self, _, factory):
        model = ModelLoader.load_model(factory)

        def is_binary_operator(node: ASTNode):
            if re.fullmatch('(?i).*binary_?operator', node.kind): yield node

        total = ASTFinder.find_all(model, is_binary_operator).count()
        assert_that(total, greater_than(0))

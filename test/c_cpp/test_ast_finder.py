import re
from pathlib import Path

import pytest
from hamcrest import assert_that, is_, greater_than, has_length

import targets
from renaissance.syntax_tree import ASTFinder, ASTNode, ASTFactory, ASTShower
from .factories import Factories




class TestFinder:
    def load_model(self,factory: ASTFactory):
        # note: make sure to load a corresponding model for the language
        return factory.create(Path(targets.__file__).parent / "main.c")


class TestKindFinder(TestFinder):

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_find_bogus(self, _, factory):
        model = self.load_model(factory)
        total = len(ASTFinder.find_kind(model, "(?i).*bogus.*"))
        assert_that(total, is_(0))

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_find_expr(self, _, factory):
        model = self.load_model(factory)
        ASTShower.show_node(model)
        assert_that(ASTFinder.find_kind(model, "(?i).*expr.*"), has_length(greater_than(0)))


class TestAllFinder(TestFinder):

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_find_all_bogus(self, _, factory):
        model = self.load_model(factory)

        def is_bogus(node: ASTNode):
            if "Bogus" in node.kind:
                yield node

        assert_that(ASTFinder.find_all(model, is_bogus), has_length(0))

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_find_all_expr(self, _, factory):
        model = self.load_model(factory)

        def is_binary_operator(node: ASTNode):
            if re.fullmatch("(?i).*binary_?operator", node.kind):
                yield node

        assert_that(ASTFinder.find_all(model, is_binary_operator), has_length(greater_than(0)))

    
    

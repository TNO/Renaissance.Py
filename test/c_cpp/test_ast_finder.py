"""Tests for finding nodes within C/C++ ASTs."""

from pathlib import Path

import pytest
from hamcrest import assert_that, greater_than, has_length, is_

import targets
from renaissance.syntax_tree import ASTFactory, ASTFinder, ASTNode, ASTShower
from renaissance.syntax_tree.ast_finder import find_nodes
from renaissance.syntax_tree.semantic_kind import SemanticKind

from .factories import Factories


class TestFinder:
    """AI: Shared base for tests that search a C/C++ AST model for nodes matching a predicate."""

    def load_model(self, factory: ASTFactory):
        """AI: Load the shared main.c model using the given AST factory."""
        # note: make sure to load a corresponding model for the language
        return factory.create(Path(targets.__file__).parent / "main.c")


class TestKindFinder(TestFinder):
    """AI: Tests ASTFinder.find single-node lookups by semantic/parser kind."""

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_find_bogus(self, _, factory):
        """AI: Verify find_nodes finds no matches for a bogus parser kind."""
        model = self.load_model(factory)
        total = len(find_nodes(model, lambda node: node.semantic_kind is SemanticKind.NODE and node.parser_kind == "BogusType"))
        assert_that(total, is_(0))

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_find_expr(self, _, factory):
        """AI: Verify find_nodes finds expression nodes in the parsed model."""
        model = self.load_model(factory)
        ASTShower.show_node(model)
        assert_that(find_nodes(model, lambda node: "EXPR" in node.parser_kind.upper()), has_length(greater_than(0)))


class TestAllFinder(TestFinder):
    """AI: Tests ASTFinder.find_all lookups against a predicate."""

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_find_all_bogus(self, _, factory):
        """AI: Verify ASTFinder.find_all finds no matches for a bogus parser kind."""
        model = self.load_model(factory)

        def is_bogus(node: ASTNode):
            if node.semantic_kind is SemanticKind.NODE and node.parser_kind == "BogusType":
                yield node

        assert_that(ASTFinder.find_all(model, is_bogus), has_length(0))

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_find_all_expr(self, _, factory):
        """AI: Verify ASTFinder.find_all finds binary operator expression nodes in the parsed model."""
        model = self.load_model(factory)

        def is_binary_operator(node: ASTNode):
            if node.semantic_kind is SemanticKind.BINARY_OPERATION:
                yield node

        assert_that(ASTFinder.find_all(model, is_binary_operator), has_length(greater_than(0)))

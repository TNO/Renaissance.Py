"""Tests for matching patterns against Clang JSON AST nodes."""

import pytest
from hamcrest import assert_that, has_length
from more_itertools import last

from renaissance.integrations.clang import CPatternFactory
from renaissance.integrations.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.ast_finder import find_nodes
from renaissance.syntax_tree.semantic_kind import SemanticKind


class TestClangJsonMatchFinder:
    """AI: Tests matching patterns against Clang JSON AST nodes."""

    @pytest.mark.skip
    def test_is_match_using_macro_from_atu(self):
        """AI: Verify a pattern derived from a translation unit's own macro matches the equivalent source usage."""
        code = """
        #define BAR "bar"
        void f(){
            const char* bar = BAR;
        }
        """
        statements = "void f() {const char* bar = BAR;}"
        factory = ASTFactory(ClangJsonASTNode, [])
        atu = factory.create_from_text(code, "test.c")
        pattern_factory = CPatternFactory(factory, ref_node=atu)
        statements_atu = pattern_factory.create(statements)
        statements = last(find_nodes(statements_atu, lambda node: node.semantic_kind is SemanticKind.STATEMENT))

        result = MatchFinder.match_pattern(atu.children, [statements])

        assert_that(result, has_length(1))

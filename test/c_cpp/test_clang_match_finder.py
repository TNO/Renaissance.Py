"""Tests for matching patterns against Clang AST nodes."""

from hamcrest import assert_that, has_length, is_

from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.ast_finder import find_nodes
from renaissance.syntax_tree.semantic_kind import SemanticKind


class ClangMatchFinderTest:
    """AI: Tests matching patterns against Clang AST nodes."""

    def test_is_match(self):
        """AI: Verify a pattern derived from a translation unit's macro matches the corresponding statement in source."""
        code = """
        #define BAR "bar"
        void g(int,int);
        int h=0;
        struct S {};

        void f(){
            const char* bar = BAR;
        }
        """
        fun = "void f() {const char* bar = BAR;  }"
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text(code, "test.c")
        pattern_factory = CPatternFactory(factory, ref_node=atu)
        statements_atu = pattern_factory.create(fun)
        statements = find_nodes(statements_atu, lambda node: node.semantic_kind is SemanticKind.STATEMENT)[-1]

        func_body = atu.children[-1].children[-1].children
        result = MatchFinder.match_pattern(func_body, [statements])
        assert_that(result, has_length(1))

    def test_typedef_in_pattern(self):
        """AI: Verify a pattern built with a typedef declaration parses without error."""
        factory = ASTFactory(ClangASTNode, [])
        pattern_factory = CPatternFactory(factory)

        pattern1 = pattern_factory.create_declarations(
            "old $name = $value;",
            extra_declarations=["typedef int old;"],
            parameters=["$value"],
        )

        assert_that(pattern1[0].children[0].name, is_("$name"))

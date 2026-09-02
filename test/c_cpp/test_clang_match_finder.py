from hamcrest import assert_that, contains_string, greater_than_or_equal_to, has_length, is_, is_in, less_than, not_none, starts_with

from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.impl.types import Declaration
from renaissance.syntax_tree import ASTFactory, MatchFinder
from renaissance.syntax_tree.ast_finder import find_ast_type


class ClangMatchFinderTest:
    def testIsMatch(self):
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
        statements = find_ast_type(statements_atu, Declaration).find_last().get()

        func_body = atu.children[-1].children[-1].children
        result = MatchFinder.match_pattern(func_body, [statements])
        assert_that(result, has_length(1))

    def test_typedef_in_pattern(self):
        factory = ASTFactory(ClangASTNode, [])
        pattern_factory = CPatternFactory(factory)

        pattern1 = pattern_factory.create_declarations(
            "old $name = $value;",
            extra_declarations=["typedef int old;"],
            parameters=["$value"],
        )

        assert_that(pattern1[0].children[0].name, is_("$name"))

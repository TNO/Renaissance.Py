from hamcrest import *
from more_itertools import last

from renaissance.impl.clang import CPatternFactory
from renaissance.impl.clang_json import ClangJsonASTNode
from renaissance.impl.types import Declaration
from renaissance.syntax_tree import ASTFactory, ASTFinder, MatchFinder
from renaissance.syntax_tree.ast_finder import find_ast_type


class TestClangJsonMatchFinder:
    def testIsMatchUsingMacroFromAtu(self):
        code = """
        #define BAR "bar"
        void f(){
            const char* bar = BAR;
        }
        """
        statements = "void f() {const char* bar = BAR;}"
        pattern_type = "(?i)Decl_?Stmt"
        factory = ASTFactory(ClangJsonASTNode, [])
        atu = factory.create_from_text(code, "test.c")
        pattern_factory = CPatternFactory(factory, ref_node=atu)
        statements_atu = pattern_factory.create(statements)
        statements = last(find_ast_type(statements_atu, Declaration))

        result = MatchFinder.match_pattern(atu.children, [statements])

        assert_that(result, has_length(1))

"""Tests for rendering C/C++ AST nodes via ASTShower."""

import pytest
from hamcrest import assert_that, contains_string, matches_regexp, not_, starts_with

from renaissance.integrations.clang import ClangASTNode, CPatternFactory
from renaissance.syntax_tree import ASTFactory, ASTShower
from renaissance.syntax_tree.ast_finder import find_nodes
from renaissance.syntax_tree.semantic_kind import SemanticKind


class TestCcppShower:
    """AI: Tests rendering C/C++ AST nodes via ASTShower."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """AI: Prepare a shared AST factory, parsed model, and pattern factory for shower tests."""
        self.factory = ASTFactory(ClangASTNode, [])
        self.atu = self.factory.create_from_text(
            """
        void ba(int i){}
        void ca(int i){}
        void lo(int i){}
        int na = 55;
        """,
            "test.c",
        )
        self.pattern_factory = CPatternFactory(self.factory, self.atu)

    def test_show_call_using_repr(self):
        """AI: Verify the string repr of a matched call node renders its signature and location."""
        pattern = self.pattern_factory.create("""
        int $xx;
        void $pa();
        void fff() {
        $pa($xx);
        }""")
        simple = find_nodes(pattern, lambda node: node.semantic_kind is SemanticKind.CALL)[0]

        assert_that(
            str(simple),
            matches_regexp("(CALL_EXPR, $pa, test.c[\\d+:\\d+]): |$pa($xx);|\n"),
        )

    def test_show_main(self):
        """AI: Verify ASTShower renders the translation unit and its top-level declarations."""
        text = ASTShower.get_node(self.atu, display_parser_kind=True)
        assert_that(text, starts_with("(TRANSLATION_UNIT,"))
        assert_that(text, contains_string("(FUNCTION_DECL, ba,"))
        assert_that(text, contains_string("(VAR_DECL, na,"))

    def test_show_body(self):
        """AI: Verify ASTShower renders each top-level declaration's body correctly."""
        assert_that(
            ASTShower.get_node(self.atu.children[0], display_parser_kind=True),
            matches_regexp("(FUNCTION_DECL, ba, test.c[\\d+:\\d+]): |void ba(int i){}|\n"),
        )
        assert_that(
            ASTShower.get_node(self.atu.children[1], display_parser_kind=True),
            matches_regexp("(FUNCTION_DECL, ca, test.c[\\d+:\\d+]): |void ca(int i){}|\n"),
        )
        assert_that(
            ASTShower.get_node(self.atu.children[2], display_parser_kind=True),
            matches_regexp("(FUNCTION_DECL, lo, test.c[\\d+:\\d+]): |void lo(int i){}|\n"),
        )
        assert_that(
            ASTShower.get_node(self.atu.children[3], display_parser_kind=True),
            matches_regexp("(VAR_DECL, na, test.c[\\d+:\\d+]): |int na = 55;|\n"),
        )

    def test_show_ast(self):
        """AI: Verify ASTShower renders the full AST including nested declarations and expressions."""
        text = ASTShower.get_node(self.atu, display_parser_kind=True)
        assert_that(text, contains_string("(TRANSLATION_UNIT,"))
        assert_that(text, contains_string("(FUNCTION_DECL, ba,"))
        assert_that(text, contains_string("(TYPE_REF, ba,"))
        assert_that(text, contains_string("(PARM_DECL, i,"))
        assert_that(text, contains_string("(COMPOUND_STMT,"))
        assert_that(text, contains_string("test.c[9:25]"))
        assert_that(text, contains_string("(VAR_DECL, na,"))
        assert_that(text, contains_string("(INTEGER_LITERAL,"))
        assert_that(text, not_(contains_string("FunctionDef")))

    def test_show_if_else(self):
        """AI: Verify ASTShower renders an if/else statement and its branches correctly."""
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text(
            """
void call(int z){
}
int main(){
int x=0,y=1;

if (x >y)
{
    x=1;
    call(x);
}
else
{
    y=1;
    call(y);
}
}
""",
            "test.c",
        )
        real_children = list(filter(lambda n: n.parser_kind != "MACRO_DEFINITION", atu.children))[1]

        ifstmt = find_nodes(real_children, lambda node: node.parser_kind == "IF_STMT")[0]
        ASTShower.show_node(ifstmt)

        text = ASTShower.get_node(ifstmt, display_parser_kind=True)
        assert_that(text, contains_string("(IF_STMT,"))
        assert_that(text, contains_string("(BINARY_OPERATOR,"))
        assert_that(text, contains_string("test.c[51:55]"))
        assert_that(text, contains_string("(COMPOUND_STMT, , test.c[57:82])"))
        assert_that(text, contains_string("(CALL_EXPR, call,"))
        assert_that(text, contains_string("|call(x);|"))
        assert_that(text, contains_string("test.c[88:113]"))
        assert_that(text, not_(contains_string("DeclarationExpression")))


if __name__ == "__main__":
    pytest.main()

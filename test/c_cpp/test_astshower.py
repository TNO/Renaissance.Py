import pytest
from hamcrest import assert_that, is_, matches_regexp, not_none

from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.impl.types import Call, If, MacroDef
from renaissance.syntax_tree import ASTFactory, ASTShower
from renaissance.syntax_tree.ast_finder import find_ast_type


class TestCcppShower:
    @pytest.fixture(autouse=True)
    def setup(self):
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
        pattern = self.pattern_factory.create("""
        int $xx;
        void $pa();
        void fff() {
        $pa($xx);
        }""")
        simple = find_ast_type(pattern, Call)[0]

        assert_that(
            str(simple),
            matches_regexp("(CALL_EXPR, $pa, test.c[\\d+:\\d+]): |$pa($xx);|\n"),
        )

    def test_show_main(self):
        expected = (
            "(TranslationUnit, test.c, test.c[0:105]):\n"
            "    ||\n"
            "    |        void ba(int i){}|\n"
            "    |        void ca(int i){}|\n"
            "    |        void lo(int i){}|\n"
            "    |        int na = 55;|\n"
            "    |        |\n"
        )
        assert_that(str(self.atu), is_(expected))

    def test_show_body(self):
        assert_that(
            str(self.atu.children[0]),
            matches_regexp("(FunctionDef, ba, test.c[\\d+:\\d+]): |void ba(int i){}|\n"),
        )
        assert_that(
            str(self.atu.children[1]),
            matches_regexp("(FunctionDef, ca, test.c[\\d+:\\d+]): |void ca(int i){}|\n"),
        )
        assert_that(
            str(self.atu.children[2]),
            matches_regexp("(FunctionDef, lo, test.c[\\d+:\\d+]): |void lo(int i){}|\n"),
        )
        assert_that(
            str(self.atu.children[3]),
            matches_regexp("(VAR_DECL, na, test.c[\\d+:\\d+]): |int na = 55;|\n"),
        )

    def test_show_ast(self):
        text = ASTShower.get_node(self.atu)
        assert_that(
            text,
            is_(
                "(TranslationUnit, test.c, test.c[0:105]):\n"
                "    ||\n"
                "    |        void ba(int i){}|\n"
                "    |        void ca(int i){}|\n"
                "    |        void lo(int i){}|\n"
                "    |        int na = 55;|\n"
                "    |        |\n"
                "  (FunctionDef, ba, test.c[9:25]): |void ba(int i){}|\n"
                "    (DeclarationLoc, ba, test.c[14:16]): |ba|\n"
                "    (TypeReference, ba, test.c[9:13]): |void|\n"
                "    (ParameterDef, i, test.c[17:22]): |int i|\n"
                "      (DeclarationLoc, i, test.c[21:22]): |i|\n"
                "      (TypeReference, i, test.c[17:20]): |int|\n"
                "    (CompoundStatement, , test.c[23:25]): |{}|\n"
                "  (FunctionDef, ca, test.c[34:50]): |void ca(int i){}|\n"
                "    (DeclarationLoc, ca, test.c[39:41]): |ca|\n"
                "    (TypeReference, ca, test.c[34:38]): |void|\n"
                "    (ParameterDef, i, test.c[42:47]): |int i|\n"
                "      (DeclarationLoc, i, test.c[46:47]): |i|\n"
                "      (TypeReference, i, test.c[42:45]): |int|\n"
                "    (CompoundStatement, , test.c[48:50]): |{}|\n"
                "  (FunctionDef, lo, test.c[59:75]): |void lo(int i){}|\n"
                "    (DeclarationLoc, lo, test.c[64:66]): |lo|\n"
                "    (TypeReference, lo, test.c[59:63]): |void|\n"
                "    (ParameterDef, i, test.c[67:72]): |int i|\n"
                "      (DeclarationLoc, i, test.c[71:72]): |i|\n"
                "      (TypeReference, i, test.c[67:70]): |int|\n"
                "    (CompoundStatement, , test.c[73:75]): |{}|\n"
                "  (VariableDef, na, test.c[84:96]): |int na = 55;|\n"
                "    (DeclarationLoc, na, test.c[88:90]): |na|\n"
                "    (TypeReference, na, test.c[84:87]): |int|\n"
                "    (Number, , test.c[93:95]): |55|\n",
            ),
        )

    def test_show_if_else(self):
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
        real_children = list(filter(lambda n: n.ast_type != MacroDef, atu.children))[1]

        ifstmt = find_ast_type(real_children, If)[0]
        ASTShower.show_node(ifstmt)

        text = ASTShower.get_node(ifstmt)
        assert_that(
            text,
            is_(
                "(If, , test.c[47:113]):\n"
                "    |if (x >y)|\n"
                "    |{|\n"
                "    |    x=1;|\n"
                "    |    call(x);|\n"
                "    |}|\n"
                "    |else|\n"
                "    |{|\n"
                "    |    y=1;|\n"
                "    |    call(y);|\n"
                "    |}|\n"
                "  (BinaryOperation, , test.c[51:55]): |x >y|\n"
                "    (Expression, x, test.c[51:52]): |x|\n"
                "      (DeclarationExpression, x, test.c[51:52]): |x|\n"
                "    (Expression, y, test.c[54:55]): |y|\n"
                "      (DeclarationExpression, y, test.c[54:55]): |y|\n"
                "  (CompoundStatement, , test.c[57:82]):\n"
                "      |{|\n"
                "      |    x=1;|\n"
                "      |    call(x);|\n"
                "      |}|\n"
                "    (BinaryOperation, , test.c[63:66]): |x=1;|\n"
                "      (DeclarationExpression, x, test.c[63:64]): |x|\n"
                "      (Number, , test.c[65:66]): |1|\n"
                "    (Call, call, test.c[72:79]): |call(x);|\n"
                "      (Expression, call, test.c[72:76]): |call|\n"
                "        (DeclarationExpression, call, test.c[72:76]): |call|\n"
                "      (Expression, x, test.c[77:78]): |x|\n"
                "        (DeclarationExpression, x, test.c[77:78]): |x|\n"
                "  (CompoundStatement, , test.c[88:113]):\n"
                "      |{|\n"
                "      |    y=1;|\n"
                "      |    call(y);|\n"
                "      |}|\n"
                "    (BinaryOperation, , test.c[94:97]): |y=1;|\n"
                "      (DeclarationExpression, y, test.c[94:95]): |y|\n"
                "      (Number, , test.c[96:97]): |1|\n"
                "    (Call, call, test.c[103:110]): |call(y);|\n"
                "      (Expression, call, test.c[103:107]): |call|\n"
                "        (DeclarationExpression, call, test.c[103:107]): |call|\n"
                "      (Expression, y, test.c[108:109]): |y|\n"
                "        (DeclarationExpression, y, test.c[108:109]): |y|\n",
            ),
        )


if __name__ == "__main__":
    pytest.main()

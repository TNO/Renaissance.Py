import unittest

import hamcrest
from hamcrest import assert_that, matches_regexp

from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.syntax_tree import ASTFactory, ASTShower, ASTFinder


class CcppShowerTest(unittest.TestCase):
    def setUp(self):
        self.factory = ASTFactory(ClangASTNode, [])
        self.atu = self.factory.create_from_text('''
        void ba(int i){}
        void ca(int i){}
        void lo(int i){}
        int na = 55;
        ''', 'test.c')
        self.pattern_factory = CPatternFactory(self.factory, self.atu)

    def test_show_call_using_repr(self):
        pattern = self.pattern_factory.create('''
        int $xx; 
        void $pa();
        void fff() {
        $pa($xx);
        }''')
        simple = ASTFinder.find_kind(pattern, '(?i)Call_?Expr').to_list()[0]

        assert_that(str(simple) , matches_regexp('(CALL_EXPR, $pa, test.c[\\d+:\\d+]): |$pa($xx);|\n'))

    def test_show_main(self):
        expected = ('(TRANSLATION_UNIT, test.c, test.c[0:105]):\n'
 '    ||\n'
 '    |        void ba(int i){}|\n'
 '    |        void ca(int i){}|\n'
 '    |        void lo(int i){}|\n'
 '    |        int na = 55;|\n'
 '    |        |\n')
        self.assertEqual(expected, str(self.atu))

    def test_show_body(self):
        expected =(('[(FUNCTION_DECL, ba, test.c[9:25]): |void ba(int i){}|\n'
         ', (FUNCTION_DECL, ca, test.c[34:50]): |void ca(int i){}|\n'
         ', (FUNCTION_DECL, lo, test.c[59:75]): |void lo(int i){}|\n'
         ', (VAR_DECL, na, test.c[84:96]): |int na = 55;|\n'
         ']'))
        real_children = list(filter(lambda n: n.kind != 'MACRO_DEFINITION', self.atu.children))
        self.assertEqual(expected, str(real_children))

    def test_show_ast_filter_implicite_Node(self):
        ptext = ASTShower.get_node(self.atu)
        self.assertIn("DECL_LOC",ptext)

    def test_show_ast(self):
        text = ASTShower.get_node(self.atu)
        self.assertEqual(('(TRANSLATION_UNIT, test.c, test.c[0:105]):\n'
 '    ||\n'
 '    |        void ba(int i){}|\n'
 '    |        void ca(int i){}|\n'
 '    |        void lo(int i){}|\n'
 '    |        int na = 55;|\n'
 '    |        |\n'
 '  (FUNCTION_DECL, ba, test.c[9:25]): |void ba(int i){}|\n'
 '    (DECL_LOC, ba, test.c[14:16]): |ba|\n'
 '    (TYPE_REF, ba, test.c[9:13]): |void|\n'
 '    (PARM_DECL, i, test.c[17:22]): |int i|\n'
 '      (DECL_LOC, i, test.c[21:22]): |i|\n'
 '      (TYPE_REF, i, test.c[17:20]): |int|\n'
 '    (COMPOUND_STMT, , test.c[23:25]): |{}|\n'
 '  (FUNCTION_DECL, ca, test.c[34:50]): |void ca(int i){}|\n'
 '    (DECL_LOC, ca, test.c[39:41]): |ca|\n'
 '    (TYPE_REF, ca, test.c[34:38]): |void|\n'
 '    (PARM_DECL, i, test.c[42:47]): |int i|\n'
 '      (DECL_LOC, i, test.c[46:47]): |i|\n'
 '      (TYPE_REF, i, test.c[42:45]): |int|\n'
 '    (COMPOUND_STMT, , test.c[48:50]): |{}|\n'
 '  (FUNCTION_DECL, lo, test.c[59:75]): |void lo(int i){}|\n'
 '    (DECL_LOC, lo, test.c[64:66]): |lo|\n'
 '    (TYPE_REF, lo, test.c[59:63]): |void|\n'
 '    (PARM_DECL, i, test.c[67:72]): |int i|\n'
 '      (DECL_LOC, i, test.c[71:72]): |i|\n'
 '      (TYPE_REF, i, test.c[67:70]): |int|\n'
 '    (COMPOUND_STMT, , test.c[73:75]): |{}|\n'
 '  (VAR_DECL, na, test.c[84:96]): |int na = 55;|\n'
 '    (DECL_LOC, na, test.c[88:90]): |na|\n'
 '    (TYPE_REF, na, test.c[84:87]): |int|\n'
 '    (INTEGER_LITERAL, , test.c[93:95]): |55|\n'), text)


    def test_show_if_else(self):
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text(
'''
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
''', 'test.c')
        real_children = list(filter(lambda n: n.kind != 'MACRO_DEFINITION', atu.children))[1]

        # expect this to work
        ifstmt = ASTFinder.find_kind(real_children, 'ifstmt').to_list()[0]

        text = ASTShower.get_node(ifstmt)
        self.assertEqual( ('(IF_STMT, , test.c[47:113]):\n'
 '    |if (x >y)|\n'
 '    |{|\n'
 '    |    x=1;|\n'
 '    |    call(x);|\n'
 '    |}|\n'
 '    |else|\n'
 '    |{|\n'
 '    |    y=1;|\n'
 '    |    call(y);|\n'
 '    |}|\n'
 '  (BINARY_OPERATOR, , test.c[51:55]): |x >y|\n'
 '    (UNEXPOSED_EXPR, x, test.c[51:52]): |x|\n'
 '      (DECL_REF_EXPR, x, test.c[51:52]): |x|\n'
 '    (UNEXPOSED_EXPR, y, test.c[54:55]): |y|\n'
 '      (DECL_REF_EXPR, y, test.c[54:55]): |y|\n'
 '  (COMPOUND_STMT, , test.c[57:82]):\n'
 '      |{|\n'
 '      |    x=1;|\n'
 '      |    call(x);|\n'
 '      |}|\n'
 '    (BINARY_OPERATOR, , test.c[63:66]): |x=1;|\n'
 '      (DECL_REF_EXPR, x, test.c[63:64]): |x|\n'
 '      (INTEGER_LITERAL, , test.c[65:66]): |1|\n'
 '    (CALL_EXPR, call, test.c[72:79]): |call(x);|\n'
 '      (UNEXPOSED_EXPR, call, test.c[72:76]): |call|\n'
 '        (DECL_REF_EXPR, call, test.c[72:76]): |call|\n'
 '      (UNEXPOSED_EXPR, x, test.c[77:78]): |x|\n'
 '        (DECL_REF_EXPR, x, test.c[77:78]): |x|\n'
 '  (COMPOUND_STMT, , test.c[88:113]):\n'
 '      |{|\n'
 '      |    y=1;|\n'
 '      |    call(y);|\n'
 '      |}|\n'
 '    (BINARY_OPERATOR, , test.c[94:97]): |y=1;|\n'
 '      (DECL_REF_EXPR, y, test.c[94:95]): |y|\n'
 '      (INTEGER_LITERAL, , test.c[96:97]): |1|\n'
 '    (CALL_EXPR, call, test.c[103:110]): |call(y);|\n'
 '      (UNEXPOSED_EXPR, call, test.c[103:107]): |call|\n'
 '        (DECL_REF_EXPR, call, test.c[103:107]): |call|\n'
 '      (UNEXPOSED_EXPR, y, test.c[108:109]): |y|\n'
 '        (DECL_REF_EXPR, y, test.c[108:109]): |y|\n'), text)


if __name__ == '__main__':
    unittest.main()

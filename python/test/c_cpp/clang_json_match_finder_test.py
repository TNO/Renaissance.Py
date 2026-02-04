from unittest import TestCase

from impl import ClangASTNode, ClangJsonASTNode
from syntax_tree import ASTFactory, ASTFinder, MatchFinder, CPatternFactory
from syntax_tree.match_finder import remove_comment_macro


class ClangMatchJsonFinderTest(TestCase):
    def testIsMatch(self):
        code = """
        #define BAR "bar"
        void f(){
            const char* bar = BAR;
        }
        """
        statements='void f() {const char* bar = BAR;}'
        pattern_type='(?i)Decl_?Stmt'
        expected = 'const char* bar = BAR;'
        factory = ASTFactory(ClangJsonASTNode, [])
        atu = factory.create_from_text(code, 'test.c')
        patternFactory = CPatternFactory(factory, ref_node=atu)
        statementsAtu = patternFactory.create(statements)
        statements = ASTFinder.find_kind(statementsAtu, pattern_type).find_last().get()
        func_body = remove_comment_macro(atu.children)#[0].children[2]
        result = MatchFinder.match_pattern(func_body, statements)
        self.assertEqual(1, len(result))

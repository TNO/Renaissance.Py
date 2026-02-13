from unittest import TestCase

from impl.clang import ClangASTNode
from syntax_tree import ASTFactory, ASTFinder, MatchFinder, CPatternFactory, ASTShower
from syntax_tree.match_finder import remove_comment_macro


class ClangMatchFinderTest(TestCase):

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
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text(code, 'test.c')
        patternFactory = CPatternFactory(factory, ref_node=atu)
        statementsAtu = patternFactory.create(statements)
        statements = ASTFinder.find_kind(statementsAtu, pattern_type).find_last().get()
        func_body = remove_comment_macro(atu.children)#[0].children[2]
        result = MatchFinder.match_pattern(func_body, [statements])
        self.assertEqual(1, len(result))
        # self.assertEqual(expected, result[0].nodes[0].text)

    def test_typedef_in_pattern(self):
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text('int f(){return 0;}', 'test.c')
        pattern_factory = CPatternFactory(factory)
        pattern1 = pattern_factory.create_declarations('old $name = $value;', extra_declarations=['typedef int old;'], parameters=['$value'])
        pattern2 = pattern_factory.create_declarations('old $name;', extra_declarations=['typedef int old;'], parameters=['$value'])

        ASTShower.show_node(pattern1[0])
        ASTShower.show_node(pattern2[0])
        self.assertEqual(pattern1[0].children[0].name,'$name')
import unittest
from unittest import TestCase

from renaissance.impl.clang import ClangASTNode
from renaissance.syntax_tree import ASTFactory, ASTFinder, MatchFinder, CPatternFactory, ASTShower
from renaissance.syntax_tree.match_finder import exclude_nodes_by_kind


class ClangMatchFinderTest(TestCase):
    # @unittest.skip("This test is currently not working, needs to be fixed")
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
        fun='void f() {const char* bar = BAR;  }'
        pattern_type='(?i)Decl_?Stmt'
        expected = 'const char* bar = BAR;'
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text(code, 'test.c')
        patternFactory = CPatternFactory(factory, ref_node=atu)
        statementsAtu = patternFactory.create(fun)
        statements = ASTFinder.find_kind(statementsAtu, pattern_type).find_last().get()
        # atu.statements[-1].body
        func_body = atu.children[-1].children[-1].children
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
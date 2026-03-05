import unittest
from unittest import TestCase

from renaissance.impl.clang_json import ClangJsonASTNode
from renaissance.syntax_tree import ASTFactory, ASTFinder, MatchFinder, CPatternFactory, ASTShower
from renaissance.syntax_tree.match_finder import exclude_nodes_by_kind


class ClangMatchJsonFinderTest(TestCase):
    @unittest.skip("marco is not detected")
    def testIsMatch(self):
        code = """
        #define BAR "bar"
        void f(){
            const char* bar = BAR;
        }
        """
        # must add define becaus e json does not include macro
        # define BAR "bar"\n
        statements='void f() {const char* bar = BAR;}'
        pattern_type='(?i)Decl_?Stmt'
        expected = 'const char* bar = BAR;'
        factory = ASTFactory(ClangJsonASTNode, [])
        atu = factory.create_from_text(code, 'test.c')
        patternFactory = CPatternFactory(factory, ref_node=atu)
        statementsAtu = patternFactory.create(statements)
        statements = ASTFinder.find_kind(statementsAtu, pattern_type).find_last().get()
        ASTShower.show_node(atu)
        ASTShower.show_node(statements)
        result = MatchFinder.match_pattern(atu.children, [statements])
        self.assertEqual(1, len(result))

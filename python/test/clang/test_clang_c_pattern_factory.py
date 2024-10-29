from impl.clang import ClangASTNode
import logging

from unittest import TestCase

from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_finder import ASTFinder
from syntax_tree.ast_shower import ASTShower
from syntax_tree.c_pattern_factory import CPatternFactory
from parameterized import parameterized
from test.c_cpp import Factories

logger = logging.getLogger(__name__)

class TestCPatternFactory(TestCase):
    pass

class TestExpression(TestCPatternFactory):

    @parameterized.expand(Factories.extend( [
        ('a == $hallo',),   
        ('2 != 3',),
        ('a != b',),
        ('b != $world',),
        ('c > $foo',),
        ('d < $bar',),
        ('e >= $baz',),
        ('f <= $qux',)
    ]))
    def test(self, _, factory, expression):
        patternFactory = CPatternFactory(factory)
        ASTShower.show_node(patternFactory.create_expression(expression))

class TestDeclaration(TestCPatternFactory):

    @parameterized.expand(Factories.extend([
        ('int a=3;',[],[],1, 0),   
        ('int a;',[],[],1, 0),   
        ('int a = $x;',[],['$x'],1,1),
        ('int a=2,b = 3;int c=4;',[],[],3,0),
        ('$type a = $x;',['$type'],['$x'],1,1),
        ('$type a,b = $x;',['$type'],['$x'],2,1),
    ]))
    def test(self, _, factory, declarationText, types, parameters, expected_vars, expected_refs):
        patternFactory = CPatternFactory(factory)
        created_declarations = list(patternFactory.create_declarations(declarationText,parameters=parameters,types=types))
        
        count_refs = 0
        count_vars = 0
        for decl in created_declarations:
            count_refs += len(list(ASTFinder.find_kind(decl, 'DECL_REF_EXPR')))
            count_vars += len(list(ASTFinder.find_kind(decl, 'VAR_DECL')))
            print('*'*80)
            ASTShower.show_node(decl)
            print('*'*80)
        self.assertEqual(count_vars, expected_vars)
        self.assertEqual(count_refs, expected_refs)

class TestStatements(TestCPatternFactory):

    @parameterized.expand(list(Factories.extend( [
        ('a=3;',[],1, 1),   
        ('a = b;',[],1, 2),   
        ('a = $x;',[],1,2),
        ('a=2;b = 3;c=4;',[],3,3),
        ('a = ($type)$x;',['$type'],1,2),
        ('a = f($x);',['f'],1,2),
    ])))
    def test(self, _, factory, statementText, types, expected_stmts, expected_refs):
        patternFactory = CPatternFactory(factory)
        created_statements = list(patternFactory.create_statements(statementText,types=types))
        
        count_refs = 0
        for decl in created_statements:
            count_refs += len(list(ASTFinder.find_kind(decl, 'DECL_REF_EXPR')))
            print('*'*80)
            ASTShower.show_node(decl)
            print('*'*80)
        self.assertEqual(len(created_statements), expected_stmts)
        self.assertEqual(count_refs, expected_refs)
        for stmt in created_statements:
            self.assertTrue(stmt.is_statement())

class Miscellaneous(TestCPatternFactory):

    def test_test(self):
        factory = ASTFactory(ClangASTNode)
        code = 'int $a;int (*fp) $f;\n\nvoid __rejuvenation__reserved__(){\n$f($a);\n}'
        atu = factory.create_from_text(code, 't.c')
        ASTShower.show_node(atu)
        atu = factory.create_from_text('class A {}; int a; int (*fp) $f; void x(){a=$f(a);}', 't.cpp')
        ASTShower.show_node(atu)
        # atu = factory.create_from_text('void f(){a();}', 't.c')
        # ASTShower.show_node(atu)

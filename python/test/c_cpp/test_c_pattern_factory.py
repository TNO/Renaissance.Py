from unittest import TestCase

from syntax_tree import ASTFinder
from syntax_tree import ASTShower
from syntax_tree import CPatternFactory
from parameterized import parameterized
from test.c_cpp.factories import Factories

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
        ('f <= $qux',),
        ('g--',),
        ('h++',),
        ('!i',)
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
            count_refs += ASTFinder.find_kind(decl, '(?i)DECL_?REF_?EXPR').count()
            count_vars += ASTFinder.find_kind(decl, '(?i)VAR_?DECL').count()
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
            count_refs += ASTFinder.find_kind(decl, '(?i)DECL_?REF_?EXPR').count()
            print('*'*80)
            ASTShower.show_node(decl)
            print('*'*80)
        self.assertEqual(len(created_statements), expected_stmts)
        self.assertEqual(count_refs, expected_refs)
        for stmt in created_statements:
            self.assertTrue(stmt.is_statement())


class TestUseAtuToCreatePatterns(TestCPatternFactory):
    """
    Test the creation of a complex pattern that includes a typedef, a struct, a define and a statement

    Complex pattern take the includes, defines and typedefs from the translation unit

    """

    @parameterized.expand(list(Factories.extend( [
        ('A a = {};',1, 1),   
        ('const char* aap=FOO;',1, 2),   
        ('const char* $x = BAR;',1,2),
    ])))
    def test(self, _, factory, statementText, expected_stmts, expected_refs):
        code = """
        #include <stdio.h>
        #define FOO "foo"
        #define BAR "bar"
        #define SAME "bar"
        typedef struct A_Struct{
            int a;
            int b;
        } A;
        int some_decl = 1; 

        void f(){
            A a = {};
            const char* aap = AAP;
            const char* noot = NOOT;
            const char* same = SAME;
            printf("%s %s %s", aap, noot, same);

        }

"""
        atu = factory.create_from_text(code, 'example.c')

        # ASTShower.show_node(atu, include_properties=True)
        # use the factory and the translation unit (for include, define and typedef reference) to create a pattern factory
        patternFactory = CPatternFactory(factory, atu)

        # pick the last statement  fo match
        pattern_root = patternFactory.create(statementText)
        ASTShower.show_node(pattern_root, include_properties=True)

        # the user must pick it's own pattern in this case the last statement
        self.assertTrue(pattern_root.get_children()[-1].is_statement())
        self.assertEqual(pattern_root.get_children()[-1].get_raw_signature() +';',statementText)

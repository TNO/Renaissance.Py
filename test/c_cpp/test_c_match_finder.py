import logging
import unittest
from unittest import TestCase
from parameterized import parameterized

from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.impl.clang_json import ClangJsonASTNode
from renaissance.syntax_tree import ASTFactory, ASTFinder, ASTShower, ASTNode, MatchFinder, PatternMatch
from renaissance.syntax_tree.match_finder import exclude_nodes_by_kind, match_pattern
from utils_for_tests import to_string, compress, show_node, debug_mismatch
from c_cpp.factories import Factories

logger = logging.getLogger(__name__)

class TestCMatchFinder(TestCase):

    SIMPLE_CPP  = """
        void f(){
            int a = 3;
            int b = 4;
            if(a == 3){
                b=5;
            }
            else{
                b--;
            }
            while(a != 3){
                if  (a == 4 && b == 5){
                    b = a;
                }
            }
        }
        """
    def test_simple_pattern(self):

        factory = ASTFactory(ClangASTNode, [])
        patterns = CPatternFactory(factory).create_statements('b--;')

        atu = factory.create_from_text('void fun(){int a,b;\nb--;\na==4;\nb==5;}', "test.c")
        matches = MatchFinder.find_all(atu.children, patterns).to_list()
        self.assertEqual(1, len(matches))


    def do_test(self, factory: ASTFactory, cpp_code, patterns:list[ASTNode], recursive: bool):
        atu = factory.create_from_text(cpp_code, "test.c")
        # find all if and while statements
        matches = MatchFinder.find_all(atu.children, patterns, recursive=recursive).filter(lambda match: match.nodes[0].is_part_of_translation_unit()).to_list()
        debug_mismatch(True, atu, patterns, matches)
        return matches

    def assert_matches(self, expected_dicts_per_match, actual_matches):
        for actual, expected_dict in zip(actual_matches, expected_dicts_per_match):
            for k, v in actual.expansions.items():
                for i,n in enumerate(v):
                    self.assertEqual(expected_dict[k][i], n.text)
        self.assertEqual(len(expected_dicts_per_match),len(actual_matches))

class TestExpressions(TestCMatchFinder):
    def test_match_expr(self):
        factory = ASTFactory(ClangJsonASTNode, [])
        exprNode = CPatternFactory(factory).create_expression('a == $x')
        ASTShower.show_node(exprNode)
        atu = factory.create_from_text('void fun(){int a,b;\nb==5;\na==3;\na==4;}', "test.c")

        show_node(atu, "CPP code")
        #find all if and while statements
        matches = MatchFinder.find_all(atu.children,[exprNode]).\
            filter(lambda match: match.nodes[0].is_part_of_translation_unit()).to_list()
        self.assertEqual(2, len(matches))


    @parameterized.expand(Factories.extend([
    ('a == 3',['a==3'], [{}]),
    ('a == $x',['a==3', 'a==4'], [{'$x':['3']},{'$x':['4']}]),
    ('$y == $x',['a==3', 'a==4', 'b==5'], [{'$y':['a'], '$x':['3']},{'$y':['a'], '$x':['4']},{'$y':['b'], '$x':['5']}]),
    ('b--',['b--;'], [{}]),
    ('b++',[], []),
    ('--b',[], []),
    ('++b',[], []),
    ('$x--',['b--;'], [{'$x': ['b']}]),
    ('$x++',[], []),
    ('--$x',[], []),
    ('++$x',[], []),
]))
    def test(self, _, factory, expression, expected_full_matches: list[str], expected_dicts_per_match: list[dict[str, list[str]]]):
        exprNode = CPatternFactory(factory).create_expression(expression)
        matches = self.do_test(factory, TestStatements.SIMPLE_CPP, [exprNode], recursive=True)
        self.assertEqual(expected_full_matches, [compress(match.nodes[0].text) for match in matches])
        self.assert_matches(expected_dicts_per_match, matches)

class TestStatements(TestCMatchFinder):
        
    @parameterized.expand(Factories.extend([
    ('$x;$y;',[{'$x': ['int a = 3;'], '$y': ['int b = 4;']}, {'$x': ['if(a == 3){\n                b=5;\n            }\n            else{\n                b--;\n            }'], '$y': ['while(a != 3){\n                if  (a == 4 && b == 5){\n                    b = a;\n                }\n            }']}]),
    ('if($x){$$stmts;}',[{'$x': ['a == 4 && b == 5'], '$$stmts': ['b = a;']}]),
    ('if($x){$$stmts;}else{$single;$$multi;}',[{'$x': ['a == 3'], '$$stmts': ['b=5;'], '$single': ['b--;'], '$$multi': []}]),
    ('if($x){$$stmts;}else{$$multi;$single;}',[{'$x': ['a == 3'], '$$stmts': ['b=5;'], '$single': ['b--;'], '$$multi': []}]),
    ('while(a!=$x){$$stmts;}',[{'$x': ['3'], '$$stmts': ['if  (a == 4 && b == 5){\n                    b = a;\n                }']}]),
]))
    def test(self, _, factory, statements, expected_dicts_per_match: list[dict[str, list[str]]]):
        patterns = CPatternFactory(factory).create_statements(statements)

        atu = factory.create_from_text(TestStatements.SIMPLE_CPP, "test.c")
        func_body = exclude_nodes_by_kind(atu.children)[0].children[2]
        matches = match_pattern( func_body.children,patterns)

        self.assert_matches( expected_dicts_per_match,matches)

class TestFunctionCallStatements(TestCMatchFinder):

    @parameterized.expand(Factories.extend([
    ('$f($a);',['int $f(int);'],[{'$f': ['one'], '$a': ['a']}]),   
    ('$f($a, $$all);',['int $f(int,int);'],[{'$f': ['one'], '$a': ['a'], '$$all': []}, {'$f': ['two'], '$a': ['a'], '$$all': ['b']}, {'$f': ['three'], '$a': ['a'], '$$all': ['b', 'c']}]),
    ('$f($$all, $a);',['int $f(int,int);'],[{'$f': ['one'], '$$all': [], '$a': ['a']}, {'$f': ['two'], '$$all': ['a'], '$a': ['b']}, {'$f': ['three'], '$$all': ['a', 'b'], '$a': ['c']}]),
    ('$f($a, $$all, $b);',['int $f(int,int,int);'],[{'$f': ['two'], '$a': ['a'], '$$all': [], '$b': ['b']}, {'$f': ['three'], '$a': ['a'], '$$all': ['b'], '$b': ['c']}]),
]))
    def test(self, _, factory, statements, extra_declarations, expected_dicts_per_match: list[dict[str, list[str]]]):
        code = """
        int one(int a);
        int two(int a, int b);
        int three(int a, int b, int c);
        int a,b,c;
        void f(){
            one(a);
            two(a,b);
            three(a,b,c);
        }
        """
        
        stmtNodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = self.do_test(factory, code, stmtNodes, recursive=True)
        self.assert_matches(expected_dicts_per_match, matches)

class TestMultiAssignments(TestCMatchFinder):

    @parameterized.expand(Factories.extend([
    ('$f($$all1);$f($$all2);',['int $f(int);'],[{'$f': ['fc'], '$$all1': ['1', '2', '3', '4', '5'], '$$all2': ['1', '2', '6', '4', '5']}]),
    # skip the advanced undeterministic all placeholder
    # ('$f($$before, $a, $$after);$f($$before, $b, $$after);',['int $f(int,int,int);'],[{'$f': ['fc'], '$$before': ['1', '2'], '$a': ['3'], '$$after': ['4', '5'], '$b': ['6']}]),
]))
    def test_args(self, _, factory, statements, extra_declarations, expected_dicts_per_match: list[dict[str, list[str]]]):
        code = """
        int fc(int a, int b, int c, int d, int e);
        int fc_else(int a, int b, int c, int d, int e);
        void f(){
            fc(1,2,3,4,5);
            fc(1,2,6,4,5);

            fc(1,2,3,4,5);
            fc_else(1,2,6,4,5);
        }
        """
        
        stmtNodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = self.do_test(factory, code, stmtNodes, recursive=True)
        self.assert_matches(expected_dicts_per_match, matches)

    @parameterized.expand(Factories.extend([
    ('if ($c) {$$before; c=3; $$after;} else {$$before; c=6; $$after;}',[],[{'$c': ['1'], '$$before': ['a=1;', 'b=2;'], '$true': ['c=3;'], '$$after': ['d=4;', 'e=5;'], '$false': ['c=6;']}]),
]))

    def test_statements(self, _, factory, statements, extra_declarations, expected_dicts_per_match: list[dict[str, list[str]]]):
        code = """
        
        void f(){
            int a,b,c,d,e;
            if(1){
               a=1;
               b=2;
               c=3;
               d=4;
               e=5;
            }
            else {
               a=1;
               b=2;
               c=6; //different
               d=4;
               e=5;
            }
        }
        """
        patterns = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        atu = factory.create_from_text(code, "test.c")
        func_body = exclude_nodes_by_kind(atu.children)[0].children[2]
        matches = match_pattern( func_body.children,patterns)



        self.assert_matches(expected_dicts_per_match,matches)

class TestUseAtuToCreatePattern(TestCMatchFinder):
    @parameterized.expand(Factories.extend([
    ('void f() {const char* bar = BAR;}','(?i)Decl_?Stmt', ['const char* bar = BAR;'], {}),
    ('void f() {const char* foo = FOO;}','(?i)Decl_?Stmt',['const char* foo = FOO;'], {}),
    ('void f() {const char* same = SAME;}','(?i)Decl_?Stmt',['const char* same = SAME;'], {}),
    ('void f() {const char* $name = BAR;}','(?i)Decl_?Stmt',['const char* bar = BAR;'], {'$name':['bar']}),
    ('void f() {const char* $name = FOO;}','(?i)Decl_?Stmt',['const char* foo = FOO;'] , {'$name':['foo']}),
    ('void f() {const char* $name = SAME;}','(?i)Decl_?Stmt',['const char* same = SAME;'], {'$name':['same']}),
    ('const char* $$args; void f() { print($$args);}','(?i)Call_?Expr',['print("%s %s %s", foo, bar, same);'], {'$$args': ['"%s %s %s"', 'foo', 'bar', 'same']}),
    ]))
    # @unittest.skip("Macro definitions are currently not included in the AST, so the test cases with FOO, BAR, SAME will fail. Need to implement macro handling first.")
    def test(self, _, factory, statements, pattern_type, expected, names):
        code = """
        #define FOO "foo"
        #define BAR "bar"
        #define SAME "bar"
        typedef struct A_Struct{
            int a;
            int b;
        } A;
        int some_decl = 1; 

        int print(const char*, ...);
        void f(){
            A a = {};
            const char* foo = FOO;
            const char* bar = BAR;
            const char* same = SAME;
            print("%s %s %s", foo, bar, same);

        }
        """
        atu = factory.create_from_text(code, 'test.c')
        patternFactory = CPatternFactory(factory, ref_node=atu) 
        statementsAtu = patternFactory.create(statements)
        statements = ASTFinder.find_kind(statementsAtu, pattern_type).find_last().get()  # pick the last statement
        # ASTShower.show_node(atu, include_properties=True)
        # ASTShower.show_node(statementsAtu, include_properties=True)
        func_body = atu.children[-1].children
        result = MatchFinder.find_all(func_body, [statements], recursive=True)
        self.assertLessEqual(1, len(result.to_list()))
        text=(result.filter(lambda match: match.patterns == names).\
            map(lambda match: match.nodes[0]).\
            filter(ASTNode.is_part_of_translation_unit).\
            map(ASTNode.text).to_list())
        # self.assertEqual(expected, text)
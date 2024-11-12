import logging
from unittest import TestCase
from parameterized import parameterized
from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_shower import ASTShower
from syntax_tree.c_pattern_factory import CPatternFactory
from syntax_tree.match_finder import MatchFinder
from syntax_tree.ast_node import ASTNode
from test.utils_for_tests import to_string, compress, show_node
from test.c_cpp.factories import Factories

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

    def do_test(self, factory: ASTFactory, cpp_code, patterns:list[ASTNode], recursive: bool):
        for idx, pattern in enumerate(patterns):
            show_node(pattern, f"Pattern[{idx}]")

        atu = factory.create_from_text(cpp_code, "test.c")

        show_node(atu, "CPP code")
        #find all if and while statements
        matches = MatchFinder.find_all([atu],patterns,recursive=recursive).to_list()
        for match in matches:
            print(f'\nmatch({[compress(p.get_raw_signature()) for p in match.patterns]})'+'{')
            print(f"  start node: {compress(match.src_nodes[0].get_raw_signature())}")
            for k, vs in match.get_nodes().items():
                # right align the key
                print(f"{k.rjust(12)}: {[compress(v.get_raw_signature()) for v in vs]}")
            print('}')
        print('    expected dict should look like:')
        print(f'      {[to_string(match.get_nodes()) for match in matches]}')
        return matches

    def assert_matches(self, matches, expected_dicts_per_match):
        for match, expected_dict in zip(matches, expected_dicts_per_match):
            self.assertDictEqual(to_string(match.get_nodes()), expected_dict)
        self.assertEqual(len(matches), len(expected_dicts_per_match))

class TestExpressions(TestCMatchFinder):
        
    @parameterized.expand(Factories.extend([
    ('a == 3',['a==3'], [{}]),   
    ('a == $x',['a==3', 'a==4'], [{'$x':['3']},{'$x':['4']}]),
    ('$y == $x',['a==3', 'a==4', 'b==5'], [{'$y':['a'], '$x':['3']},{'$y':['a'], '$x':['4']},{'$y':['b'], '$x':['5']}]),
    ('b--',['b--'], [{}]),
    ('b++',[], []),
    ('--b',[], []),
    ('++b',[], []),
    ('$x--',['b--'], [{'$x': ['b']}]),
    ('$x++',[], []),
    ('--$x',[], []),
    ('++$x',[], []),
]))
    def test(self, _, factory, expression, expected_full_matches: list[str], expected_dicts_per_match: list[dict[str, list[str]]]):
        exprNode = CPatternFactory(factory).create_expression(expression)
        matches = self.do_test(factory, TestStatements.SIMPLE_CPP, [exprNode], recursive=True)
        self.assertEqual([compress(match.src_nodes[0].get_raw_signature()) for match in matches], expected_full_matches)
        self.assert_matches(matches, expected_dicts_per_match)

class TestStatements(TestCMatchFinder):
        
    @parameterized.expand(Factories.extend([
    ('$x;$y;',[{'$x': ['int a=3;'], '$y': ['int b=4;']}, {'$x': ['if(a==3){b=5;}else{b--;}'], '$y': ['while(a!=3){if(a==4&&b==5){b=a;}}']}]),   
    ('if($x){$$stmts;}',[{'$x': ['a==4&&b==5'], '$$stmts': ['b=a']}]),
    ('if($x){$$stmts;}else{$single;$$multi}',[{'$x': ['a==3'], '$$stmts': ['b=5'], '$single': ['b--'], '$$multi': []}]),
    ('if($x){$$stmts;}else{$$multi;$single;}',[{'$x': ['a==3'], '$$stmts': ['b=5'], '$single': ['b--'], '$$multi': []}]),
    ('while(a!=$x){$$stmts;}',[{'$x': ['3'], '$$stmts': ['if(a==4&&b==5){b=a;}']}]),
]))
    def test(self, _, factory, statements, expected_dicts_per_match: list[dict[str, list[str]]]):
        stmtNodes = CPatternFactory(factory).create_statements(statements)
        matches = self.do_test(factory, TestStatements.SIMPLE_CPP, stmtNodes, recursive=True)  # type: ignore
        self.assert_matches(matches, expected_dicts_per_match)

class TestFunctionCallStatements(TestCMatchFinder):

    @parameterized.expand(Factories.extend([
    ('$f($a);',['int (*fp) $f;'],[{'$f': ['one'], '$a': ['a']}]),   
    ('$f($a, $$all);',['int (*fp) $f;'],[{'$f': ['one'], '$a': ['a'], '$$all': []}, {'$f': ['two'], '$a': ['a'], '$$all': ['b']}, {'$f': ['three'], '$a': ['a'], '$$all': ['b', 'c']}]),
    ('$f($$all, $a);',['int (*fp) $f;'],[{'$f': ['one'], '$$all': [], '$a': ['a']}, {'$f': ['two'], '$$all': ['a'], '$a': ['b']}, {'$f': ['three'], '$$all': ['a', 'b'], '$a': ['c']}]),
    ('$f($a, $$all, $b);',['int (*fp) $f;'],[{'$f': ['two'], '$a': ['a'], '$$all': [], '$b': ['b']}, {'$f': ['three'], '$a': ['a'], '$$all': ['b'], '$b': ['c']}]),
]))
    def test(self, _, factory, statements, extra_declarations, expected_dicts_per_match: list[dict[str, list[str]]]):
        code = """
        int one(int a);
        int two(int a, int b);
        int three(int a, int b, int c);
        int a,b,c;
        void f(){
            one(a);
            two(a,b)
            three(a,b,c);
        }
        """
        
        stmtNodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = self.do_test(factory, code, stmtNodes, recursive=True) # type: ignore
        self.assert_matches(matches, expected_dicts_per_match)

class TestMultiAssignments(TestCMatchFinder):

    @parameterized.expand(Factories.extend([
    ('$f($$all1);$f($$all2)',['int (*fp) $f;'],[{'$f': ['fc'], '$$all1': ['1', '2', '3', '4', '5'], '$$all2': ['1', '2', '6', '4', '5']}]),   
    ('$f($$before, $a, $$after);$f($$before, $b, $$after)',['int (*fp) $f;'],[{'$f': ['fc'], '$$before': ['1', '2'], '$a': ['3'], '$$after': ['4', '5'], '$b': ['6']}]),   
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
        matches = self.do_test(factory, code, stmtNodes, recursive=True) # type: ignore
        self.assert_matches(matches, expected_dicts_per_match)

    @parameterized.expand(Factories.extend([
    ('if ($c) {$$before; $true; $$after;} else {$$before; $false; $$after;}',['int (*fp) $f;'],[{'$c': ['1'], '$$before': ['a=1', 'b=2'], '$true': ['c=3'], '$$after': ['d=4', 'e=5'], '$false': ['c=6']}]),   
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
        
        stmtNodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = self.do_test(factory, code, stmtNodes, recursive=True) # type: ignore
        self.assert_matches(matches, expected_dicts_per_match)

class TestComposeReplacement(TestCMatchFinder):

    @parameterized.expand(Factories.extend([
    ('if($exp){$$before;b=$d1;$$after;}else{$$before;b=$d2;$$after;}',[],{'$$before; b = ($exp) ? $d1:$d2; $$after;': "c++; b = (a==1) ? 2:3; d++;"}),   
]))
    def test_args(self, _, factory, statements, extra_declarations, replacement: dict[str, str]):
        code = """
        int a = 1;
        int b = 2;
        int c = 3;
        int d = 4;
        void f(){
            if (a==1) {
                c++;
                b = 2;
                d++;
            }
            else {
                c++;
                b = 3;
                d++;
            }
        }
        """
        
        stmtNodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = self.do_test(factory, code, stmtNodes, recursive=True) # type: ignore
        for match, exp in zip(matches, replacement.items()):
            org, expected = exp
            actual = match.compose_replacement(org)
            self.assertEqual(actual, expected)  


import logging
from unittest import TestCase
from parameterized import parameterized
from syntax_tree.ast_factory import ASTFactory
from syntax_tree.c_pattern_factory import CPatternFactory
from syntax_tree.match_finder import MatchFinder
from syntax_tree.ast_node import ASTNode
from test.test_utils import to_string, compress, show_node


from test.c_cpp import Factories

logger = logging.getLogger(__name__)

class TestMatchFinder(TestCase):

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

    def do_test(self, factory: ASTFactory, cpp_code, patterns:list[ASTNode], expected_dicts_per_match: list[dict[str, list[str]]] ,recursive: bool):
        for idx, pattern in enumerate(patterns):
            show_node(pattern, f"Pattern[{idx}]")

        atu = factory.create_from_text(cpp_code, "test.cpp")
        show_node(atu, "CPP code")
        #find all if and while statements
        matches = list(MatchFinder.find_all([atu],patterns,recursive=recursive))
        for match in matches:
            print(f'\nmatch({[compress(p.get_raw_signature()) for p in match.patterns]})'+'{')
            print(f"  start node: {compress(match.src_nodes[0].get_raw_signature())}")
            for k, vs in match.get_dict().items():
                # right align the key
                print(f"{k.rjust(12)}: {[compress(v.get_raw_signature()) for v in vs]}")
            print('}')
        print('    expected dict should look like:')
        print(f'      {[to_string(match.get_dict()) for match in matches]}')
        for match, expected_dict in zip(matches, expected_dicts_per_match):
            self.assertDictEqual(to_string(match.get_dict()), expected_dict)
        self.assertEqual(len(matches), len(expected_dicts_per_match))
        return matches

class TestExpressions(TestMatchFinder):
        
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
        matches = self.do_test(factory, TestStatements.SIMPLE_CPP, [exprNode], expected_dicts_per_match, recursive=True)
        self.assertEqual([compress(match.src_nodes[0].get_raw_signature()) for match in matches], expected_full_matches)

class TestStatements(TestMatchFinder):
        
    @parameterized.expand(Factories.extend([
    ('$x;$y;',[{'$x': ['int a=3;'], '$y': ['int b=4;']}, {'$x': ['if(a==3){b=5;}else{b--;}'], '$y': ['while(a!=3){if(a==4&&b==5){b=a;}}']}]),   
    ('if($x){$$stmts;}',[{'$x': ['a==4&&b==5'], '$$stmts': ['b=a']}]),
    ('if($x){$$stmts;}else{$single;$$multi}',[{'$x': ['a==3'], '$$stmts': ['b=5'], '$single': ['b--'], '$$multi': []}]),
    ('if($x){$$stmts;}else{$$multi;$single;}',[{'$x': ['a==3'], '$$stmts': ['b=5'], '$single': ['b--'], '$$multi': []}]),
    ('while(a!=$x){$$stmts;}',[{'$x': ['3'], '$$stmts': ['if(a==4&&b==5){b=a;}']}]),
]))
    def test(self, _, factory, statements, expected_dicts_per_match: list[dict[str, list[str]]]):
        stmtNodes = CPatternFactory(factory).create_statements(statements)
        self.do_test(factory, TestStatements.SIMPLE_CPP, stmtNodes, expected_dicts_per_match, recursive=True)

class TestFunctionCallStatements(TestMatchFinder):

    @parameterized.expand(Factories.extend([
    ('$f($a);',['int (*fp) $f;'],[{'$f': ['one(a)'], '$a': ['a']}]),   
    ('$f($a, $$all);',['int (*fp) $f;'],[{'$f': ['one(a)'], '$a': ['a'], '$$all': []}, {'$f': ['two(a,b)'], '$a': ['a'], '$$all': ['b']}, {'$f': ['three(a,b,c)'], '$a': ['a'], '$$all': ['b', 'c']}]),
    ('$f($$all, $a);',['int (*fp) $f;'],[{'$f': ['one(a)'], '$$all': [], '$a': ['a']}, {'$f': ['two(a,b)'], '$$all': ['a'], '$a': ['b']}, {'$f': ['three(a,b,c)'], '$$all': ['a', 'b'], '$a': ['c']}]),
    ('$f($a, $$all, $b);',['int (*fp) $f;'],[{'$f': ['two(a,b)'], '$a': ['a'], '$$all': [], '$b': ['b']}, {'$f': ['three(a,b,c)'], '$a': ['a'], '$$all': ['b'], '$b': ['c']}]),
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
        self.do_test(factory, code, stmtNodes, expected_dicts_per_match, recursive=True)


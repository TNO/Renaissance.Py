import ast
import unittest
from _ast import AST
from typing import Sequence

from impl import PythonASTNode, PythonPatternFactory
from impl.python import match_pattern, find_all, match
from syntax_tree import ASTFactory, MatchFinder, ASTShower


class PythonShowerTest(unittest.TestCase):
    def test_show_call(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$pa($55)')
        text = ASTShower.get_node(simple)
        self.assertEqual(
            '''
            (Expr, _MatchOne__pa, None[100000:200028]): |_MatchOne__pa(_MatchOne__55)|
            (Call, _MatchOne__pa, None[0:0]): |_MatchOne__pa(_MatchOne__55)|
             (Name, _MatchOne__pa, None[0:0]): |_MatchOne__pa|
             (ImplesiteType, , None[0:0]): ||),text)
        ''', text)


    def test_show_if_else(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text(
'''
if x >y :
    x=1
    call(x)
else:
    y=1
    call(y)    
''', 'test.py')
        text = ASTShower.get_node(atu)
        self.assertEqual(
            '''
            (Expr, _MatchOne__pa, None[100000:200028]): |_MatchOne__pa(_MatchOne__55)|
            (Call, _MatchOne__pa, None[0:0]): |_MatchOne__pa(_MatchOne__55)|
             (Name, _MatchOne__pa, None[0:0]): |_MatchOne__pa|
             (ImplesiteType, , None[0:0]): ||),text)
        ''', text)


if __name__ == '__main__':
    unittest.main()

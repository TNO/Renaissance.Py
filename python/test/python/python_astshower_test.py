import ast
import unittest
from _ast import AST
from typing import Sequence

from impl import PythonASTNode, PythonPatternFactory
from impl.python import match_pattern, find_all, match
from syntax_tree import ASTFactory, MatchFinder, ASTShower


class PythonShowerTest(unittest.TestCase):
    def setUp(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.atu = self.factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        self.pattern_factory = PythonPatternFactory(self.factory, self.atu)

    def test_show_call_using_repr(self):
        simple = self.pattern_factory.create('$pa($55)')
        self.assertEqual('(Expr, $pa($55), None[0:0]): \n|_MatchOne__pa(_MatchOne__55)|\n', str(simple))

    def test_show_module(self):
        text = ASTShower.get_node(self.atu)
        expected = '(Module, Module, test.py[0:29]): \n|ba(55)|\n|ca(555)|\n|lo(4444)|\n|na = 55|\n'
        self.assertEqual(expected, str(self.atu))
    def test_show_body(self):
        text = ASTShower.get_node(self.atu)
        expected =('[(Expr, ba(55), test.py[0:6]): \n'    '|ba(55)|\n'
                 ', (Expr, ca(555), test.py[7:7]): \n'    '|ca(555)|\n'
                 ', (Expr, lo(4444), test.py[15:8]): \n'  '|lo(4444)|\n'
                 ', (Assign, na = 55, test.py[24:5]): \n' '|na = 55|\n'
                 ']')

        self.assertEqual(expected, str(self.atu.get_children()))

    def test_show_ast_a_b(self):
        text = ASTShower.get_node(self.atu)
        ptext = ASTShower.get_python_node(self.atu)
        self.assertEqual(text+"a",ptext)

    def test_show_ast_filter_implicite_Node(self):

        ptext = ASTShower.get_python_node(self.atu)
        self.assertNotIn("ImplicitNode",ptext)

    def test_show_ast(self):
        text = ASTShower.get_node(self.atu)
        self.assertEqual('', text)


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
        text = ASTShower.get_python_node(atu.get_children()[0])
        self.assertEqual( "", text)


if __name__ == '__main__':
    unittest.main()

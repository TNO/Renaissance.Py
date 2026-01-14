import ast
import unittest
from _ast import AST
from typing import Sequence

from impl import PythonASTNode, PythonPatternFactory
from impl.python import match_pattern, find_all, match
from syntax_tree import ASTFactory, MatchFinder, ASTShower


class PythonShowerTest(unittest.TestCase):
    def test_not_equal_nodes(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$pa($55)')
        text = ASTShower.get_node(simple)
        text2 = ast.dump(simple.node)
        self.assertEqual(text2,text)

if __name__ == '__main__':
    unittest.main()

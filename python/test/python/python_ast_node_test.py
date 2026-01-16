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
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'apple.py')
        second_stmt = atu.get_children()[1]
        self.assertEqual(7,second_stmt.get_start_offset())
        self.assertEqual (7, second_stmt.get_length())
        self.assertEqual('apple.py', second_stmt.get_containing_filename())
        self.assertEqual(atu.translation_unit, second_stmt.translation_unit)
if __name__ == '__main__':
    unittest.main()

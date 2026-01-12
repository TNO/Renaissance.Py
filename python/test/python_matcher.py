import ast
import unittest
from typing import Sequence

from impl import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTFactory, MatchFinder


class MyTestCase(unittest.TestCase):
    def test_something(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(ss)\nif pa(ss):\n  pa(ss)\n  pa=ss', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(ss)')
        result = MatchFinder.find_all(atu, simple).to_list()
        self.assertGreater(len(result),0)

    def test_match_all(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(55)')
        results = MatchFinder.match_pattern( atu.get_children(), simple, lambda n: n )
        for res in results:
            print( str(res))
        self.assertGreater(len(results),0)

    def test_ast_name(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(55)')
        self.assertEqual(simple.get_name(),'pa')


    def test_python_ast_name(self):
        simple = ast.parse('pa(55)').body[0]
        assert(simple.value.func.id == 'pa')


if __name__ == '__main__':
    unittest.main()

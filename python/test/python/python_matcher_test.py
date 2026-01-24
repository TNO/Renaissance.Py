import ast
import unittest
from typing import Sequence

import impl.python.python_ast_node
from impl import PythonASTNode, PythonPatternFactory
from impl.python import match_pattern, find_all, match
from syntax_tree import ASTFactory, MatchFinder
from syntax_tree.match_finder import MatchUtils


class PythonMatcherTest(unittest.TestCase):
    def test_match_pattern(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$pa($55)')
        result = find_all(atu, [simple]).to_list()
        self.assertEqual(1,len(result))


    def test_generic_is_match_stmt(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$pa(55)')
        self.assertEqual('Expr', simple.get_kind())
        self.assertTrue(MatchUtils.is_match(atu.get_children()[0], simple))

    def test_generic_is_match_assignment(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('na=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$pa')
        self.assertEqual('_MatchOne__', simple.get_kind())
        self.assertTrue(MatchUtils.is_match(atu.get_children()[0], simple))

    def test_match_stmt_using_generic_matcher(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$pa')
        result = MatchFinder.find_all(atu, [simple]).to_list()
        # TODO because ther is no distinction between Expr and stmt should be 4
        self.assertEqual(7,len(result))

    def test_find_all_using_generic_matcher(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$pa(55)')
        self.assertTrue(MatchUtils.is_match(atu.get_children()[0], simple))
        self.assertFalse(MatchUtils.is_match(atu.get_children()[1], simple))
        self.assertFalse(MatchUtils.is_match(atu.get_children()[2], simple))
        self.assertFalse(MatchUtils.is_match(atu.get_children()[3], simple))
        result = MatchFinder.find_all(atu.get_children(), [simple]).to_list()
        self.assertEqual(1,len(result))


    def test_match_fun_pattern_using_generic_matcher(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$ca($sss)')
        result = MatchFinder.find_all(atu, [simple]).to_list()
        self.assertEqual(3, len(result))

    def test_match_fun_using_generic_matcher(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('ca(555)')
        result = MatchFinder.find_all(atu, [simple]).to_list()
        self.assertEqual(1, len(result))

    def test_match_multi_fun_using_generic_matcher(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('ba(55)\nca(555)')
        result = MatchFinder.find_all(atu, [simple]).to_list()
        self.assertEqual(1, len(result))

    def test_match_multi_fun_using_generic_matcher(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('ba(55)\nca(555)')
        result = MatchFinder.find_all(atu, [simple]).to_list()
        self.assertEqual(1, len(result))

    def test_match_flat(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\npa(55)\npa(55)\npa=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(55)')
        results = match_pattern( atu.get_children(), [simple] )
        for res in results:
            print( str(res))
        self.assertEqual(len(results),3)

    def test_match_multiple(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create_statements('ba($a)\nna($b)\nna($c)')
        results = match_pattern( atu.get_children(), simple )
        self.assertEqual(len(results[0]),3)
        self.assertEqual(len(results),2)

    def test_match_different_placeholder(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(51)\nna(52)\nna(53)\npa(54)\npa(55)\nba(56)\nna(57)\nna(58)\nna=59\nba(51)\nna(52)\nna(53)\n', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create_statements('ba($a)\nna($b)\nna($c)')
        results = match_pattern( atu.get_children(), simple )
        self.assertEqual(len(results),2)
        self.assertEqual(len(results[0]),3)

    def test_match_recursion_placeholder(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(51)\nna(52)\nna(53)\npa(54)\nif pa(55):\n  ba(51)\n  na(52)\n  na(53)\n  na=59\nelse:\n  ba(51)\n  na(52)\n  na(53)\n', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create_statements('ba($a)\nna($b)\nna($c)')
        results = match_pattern( atu.get_children(), simple )
        self.assertEqual(3,len(results),)
        self.assertEqual(3,len(results[0]))

    def test_match_any_placeholder(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('''
ba()
na()  
ba()
pa(54)
ba()  
na()  
ba()
na()  
na=59
ba()  
na()
ba()

''', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create_statements('ba($a)\n$$na\nba($c)')
        results = match_pattern( atu.get_children(), simple )
        self.assertEqual(3,len(results),)
        self.assertEqual(3, len(results[0]),)

    def test_match_any_placeholder_but_different_content(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text(
'''
ba(51)
na(52)  
na(52)  
na(53)
ba(53)
pa(54)
if pa(55):
    ba(51)  
    na(52)  
    na(53)
    ba(53)
    na(53)  
    na=59
else:  
    ba(51)  
    na(52)  
    ba(53)

''', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create_statements('ba($a)\n$$na\nba($c)')
        results = match_pattern(atu.get_children(), simple)
        self.assertEqual(1,len(results), )
        self.assertEqual(5, len(results[0]), )

    def test_match_any_placeholder_but_in_child(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text(
'''
ba()
ca()  
lo()  
na()
ba()
pa()
if pa():
    ba()  
    ca()  
    lo()
    na()
    na()  
    na=59
else:  
    ba()  
    na()  
    ba()

''', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create_statements('ba()\n$$na\nna()')
        results = match_pattern(atu.get_children(), simple)
        self.assertEqual(2, len(results), )
        self.assertEqual(4, len(results[0]), )

    def test_match_all_epression(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  if pa(55):\n    pa(55)\n  pa=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(55)')
        results = MatchFinder.match_pattern( atu.get_children(), PythonASTNode(simple.node.value) )
        self.assertEqual(5,len(results))

    def test_match_all_statement(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  if pa(55):\n    pa(55)\n  pa=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(55)')
        results = match_pattern( atu.get_children(), [simple] )
        self.assertEqual(3,len(results))

    def test_ast_name(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(55)')
        self.assertEqual('pa(55)', simple.get_name())


    def test_python_ast_name(self):
        simple = ast.parse('pa(55)').body[0]
        assert(simple.value.func.id == 'pa')

    def test_equal_nodes(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(55)')
        self.assertTrue(match(simple.node,atu.get_children()[0].node))

    def test_equal_nodes_different_args(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(66)')
        self.assertFalse(match(simple,atu.get_children()[0]))

    def test_call_has_args_as_children(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('pa(66)')
        self.assertGreater(len(simple.expression.get_children()),0)

    def test_not_equal_nodes(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('pap(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('ma(55)')
        self.assertFalse(match(simple,atu.get_children()[0]))

    def test_replace_multiple_different_nodes(self):

        example_code = """
        from module import foo, bar, baz, quux
        ba(51)
        na(52)
        na(53)
        pa(54)
        if pa():
          ba()
        
        if pa(55):
          ba(51)
          na(52)
          na(53)
          na=59
        else:
          ba(51)
          na(52)
          na(53)
        
        """.strip()
if __name__ == '__main__':
    unittest.main()

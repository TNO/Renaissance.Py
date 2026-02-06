import ast
import inspect
import unittest
from unittest.mock import patch

from impl import PythonASTNode, PythonPatternFactory, MATCH_ALL, MATCH_ONE
from syntax_tree import ASTFactory, MatchFinder
from syntax_tree.match_finder import is_match, PatternMatch


class PythonMatcherTest(unittest.TestCase):

    def setUp(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.atu = self.factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        self.pattern_factory = PythonPatternFactory(self.factory, self.atu)

    def test_kind_is_match_one(self):
        simple = self.pattern_factory.create('$pa')
        self.assertEqual(MATCH_ONE, simple.kind)

    def test_kind_is_match_all(self):
        simple = self.pattern_factory.create('$$pa')
        self.assertEqual(MATCH_ALL, simple.kind)

    def test_match_one_stmt(self):
        simple = self.pattern_factory.create('$pa')
        self.assertTrue(is_match(self.atu.children[0], simple, {}))

    def test_is_match_all_stmt(self):
        simple = self.pattern_factory.create('$$pa')
        self.assertTrue(MatchFinder.match_pattern(self.atu.children, simple))

    def test_is_exact_match(self):
        simple = self.pattern_factory.create('ba(55)')
        self.assertTrue(is_match(self.atu.children[0], simple))

    def test_match_exact_pattern(self):
        simple = self.pattern_factory.create('ba(55)')

        result = MatchFinder.match_pattern(self.atu, simple)
        self.assertEqual(1, len(result))

    def test_find_all_exact_match(self):
        simple = self.pattern_factory.create('ba(55)')
        result = MatchFinder.find_all(self.atu, [simple]).to_list()
        self.assertEqual(1, len(result))

    def test_match_single_pattern(self):
        simple = self.pattern_factory.create('$stmt')
        result = MatchFinder.match_pattern(self.atu, simple)
        self.assertEqual(4, len(result))

    def test_match_single_call_pattern(self):
        simple = self.pattern_factory.create('$call($arg)')

        result = MatchFinder.match_pattern(self.atu, simple)
        self.assertEqual(3, len(result))

    def test_find_all_cakks_match_pattern(self):
        simple = self.pattern_factory.create('$stmt')
        with patch.object(MatchFinder, 'match_pattern') as mock_match_pattern:
            MatchFinder.find_all(self.atu, [simple]).to_list()
            mock_match_pattern.assert_called_once_with([self.atu], [simple])

    def test_match_pattern(self):
        simple = self.pattern_factory.create('$pa($55)')
        result = MatchFinder.find_all(self.atu, [simple]).to_list()
        self.assertEqual(3, len(result))

    def test_generic_is_match_assignment(self):
        atu = self.factory.create_from_text('na=55', 'test.py')
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create('$pa')
        self.assertEqual('_MatchOne__', simple.kind)
        self.assertTrue(is_match(atu.children[0], simple, {}))

    def test_find_all_using_generic_matcher(self):
        simple = self.pattern_factory.create('$pa(55)')

        self.assertTrue(is_match(self.atu.children[0], simple))
        self.assertFalse(is_match(self.atu.children[1], simple))
        self.assertFalse(is_match(self.atu.children[2], simple))
        self.assertFalse(is_match(self.atu.children[3], simple))

        result = MatchFinder.match_pattern(self.atu.children, simple)  # .to_list()
        self.assertEqual(1, len(result))

    def test_match_one_fun_pattern_using_generic_matcher(self):
        simple = self.pattern_factory.create('$ca($sss)')
        result = MatchFinder.find_all(self.atu, [simple]).to_list()
        self.assertEqual(3, len(result))

    def test_match_fun_using_generic_matcher(self):
        simple = self.pattern_factory.create('ca(555)')
        result = MatchFinder.find_all(self.atu, [simple]).to_list()
        self.assertEqual(1, len(result))

    def test_match_multi_fun_using_generic_matcher(self):
        simple = self.pattern_factory.create('ba(55)\nca(555)')
        result = MatchFinder.find_all(self.atu, [simple]).to_list()
        self.assertEqual(1, len(result))

    def test_match_multi_fun_using_generic_matcher(self):
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations

        simple = self.pattern_factory.create('ba(55)\nca(555)')
        result = MatchFinder.find_all(self.atu, [simple]).to_list()
        self.assertEqual(1, len(result))

    def test_match_flat(self):
        atu = self.factory.create_from_text('pa(55)\npa(55)\npa(55)\npa=55', 'test.py')

        simple = self.pattern_factory.create('pa(55)')

        results = MatchFinder.match_pattern(atu.children, [simple])
        for res in results:
            print(str(res))
        self.assertEqual(len(results), 3)

    def test_match_multiple(self):
        atu = self.factory.create_from_text('ba(55)\nna(55)\nna(55)\npa(55)\npa(55)\nba(55)\nna(55)\nna(55)\nna=55',
                                            'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create_statements('ba($a)\nna($b)\nna($c)')

        results = MatchFinder.match_pattern(atu.children, simple)
        self.assertEqual(len(results[0].nodes), 3)
        self.assertEqual(len(results), 2)

    def test_match_different_placeholder(self):
        atu = self.factory.create_from_text(
            'ba(51)\nna(52)\nna(53)\npa(54)\npa(55)\nba(56)\nna(57)\nna(58)\nna=59\nba(51)\nna(52)\nna(53)\n',
            'test.py')
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create_statements('ba($a)\nna($b)\nna($c)')

        results = MatchFinder.match_pattern(atu.children, simple)
        self.assertEqual(3, len(results))
        self.assertEqual(3, len(results[0].nodes))

    def test_match_recursion_placeholder(self):
        atu = self.factory.create_from_text(
            'ba(51)\nna(52)\nna(53)\npa(54)\nif pa(55):\n  ba(51)\n  na(52)\n  na(53)\n  na=59\nelse:\n  ba(51)\n  na(52)\n  na(53)\n',
            'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create_statements('ba($a)\nna($b)\nna($c)')

        results = MatchFinder.match_pattern(atu.children, simple)
        self.assertEqual(3, len(results), )
        self.assertEqual(3, len(results[0].nodes))

    def test_match_any_placeholder(self):
        atu = self.factory.create_from_text('''
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
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create_statements('ba()\n$$na\nba()')

        results = MatchFinder.match_pattern(atu.children, simple)
        self.assertEqual(3, len(results), )
        self.assertEqual(3, len(results[0].nodes), )

    def test_match_any_placeholder_but_different_content(self):
        atu = self.factory.create_from_text(
            inspect.cleandoc('''
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
                    na=599
                else:  
                    ba(51)  
                    na(52)  
                    ba(53)
                
                '''), 'test.py')

        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create_statements('ba($a)\n$$na\nba($c)')

        results = MatchFinder.match_pattern(atu.children, simple)
        self.assertEqual(3, len(results))
        self.assertEqual(5, len(results[0].nodes))

    def test_match_any_placeholder_but_in_child(self):
        atu = self.factory.create_from_text(inspect.cleandoc(
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
            
            '''), 'test.py')

        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create_statements('ba()\n$$na\nna()')

        results = MatchFinder.match_pattern(atu.children, simple)
        self.assertEqual(3, len(results), )
        self.assertEqual(4, len(results[0].nodes), )

    # can only return one match
    def test_match_all_epression(self):
        atu = self.factory.create_from_text('pa(55)\npa(55)\nif pa(55):\n  pa(55)\n  if pa(55):\n    pa(55)\n  pa=55',
                                            'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create('pa(55)')

        results = MatchFinder.match_pattern(atu.children, simple)
        # 4 because the one in if is a expression
        self.assertEqual(4, len(results))

    def test_match_all_statement(self):
        atu = self.factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  if pa(55):\n    pa(55)\n  pa=55',
                                            'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create('pa(55)')

        results = MatchFinder.match_pattern(atu.children, [simple])
        self.assertEqual(3, len(results))

    def test_ast_name(self):
        atu = self.factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create('pa(55)')
        self.assertEqual('pa(55)', simple.name)

    def test_python_ast_name(self):
        simple = ast.parse('pa(55)').body[0]
        assert (simple.value.func.id == 'pa')

    def test_eq_nodes(self):
        atu = self.factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create('pa(55)')
        self.assertTrue(simple == atu.children[0])

    def test_not_eq_nodes(self):
        atu = self.factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create('ma(55)')
        self.assertFalse(simple == atu.children[0])

    def test_nodes_is_not_matching_when_different_args(self):
        atu = self.factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create('pa(66)')
        self.assertFalse(simple == atu.children[0])

    def test_call_has_args_as_children(self):
        atu = self.factory.create_from_text('pa(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(self.factory, atu)
        simple = pattern_factory.create('pa(66,77,88)')
        self.assertEqual(len(simple.children[0].children[1].children), 3)

    def test_not_equal_nodes(self):
        self.atu = self.factory.create_from_text('pap(55)\nif pa(55):\n  pa(55)\n  pa=55', 'test.py')
        pattern_factory = PythonPatternFactory(self.factory, self.atu)
        simple = pattern_factory.create('ma(55)')
        self.assertFalse(simple == self.atu.children[0])

    def test_match_any_with_empty(self):
        example_code = """
ba()
na()        
"""
        self.atu = self.factory.create_from_text(example_code, 'test.py')
        simple = self.pattern_factory.create_statements('ba()\n$$any\nna()')

        results = MatchFinder.match_pattern(self.atu.children, simple)
        self.assertEqual(1, len(results), )
        res = results[0]
        self.assertIsInstance(res, PatternMatch)
        self.assertEqual(2, len(res.nodes))
        self.assertEqual(1, len(res.expansions))
        self.assertEqual([], res.expansions['$$any'])

        def test_match_any_with_multiple(self):
            example_code = """
ba()
ca()
lo()
na()
"""
            # if pa():
            #   ba()
            #   na()
            # if pa():
            # else:
            #   ba()
            #   la()
            #   ri()
            #   na()
            self.atu = self.factory.create_from_text(example_code, 'test.py')
            simple = self.pattern_factory.create_statements('ba()\n$$any\nna()')

            results = MatchFinder.match_pattern(self.atu.children, simple)
            self.assertEqual(1, len(results), )
            res = results[0]
            self.assertIsInstance(res, PatternMatch)
            self.assertEqual(2, len(res.nodes))
            self.assertEqual(1, len(res.expansion_lists))
            self.assertEqual([], res.expansion_lists['$$any'])


if __name__ == '__main__':
    unittest.main()

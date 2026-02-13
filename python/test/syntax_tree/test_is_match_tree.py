import ast
import unittest

import pytest

from impl.clang import ClangASTNode
from impl.clang_json import ClangJsonASTNode
from impl.python import PythonASTNode, PythonPatternFactory
from syntax_tree import ASTFactory, MatchFinder, CPatternFactory
from syntax_tree.ast_node import MATCH_ALL, MATCH_ONE
from syntax_tree.match_finder import is_match_tree, find_in_list


def test_none_with_none():
    src = None
    pattern = None
    assert is_match_tree(src, pattern)


def test_none_with_list():
    src = None
    pattern = [1]
    assert not is_match_tree(src, pattern)


def test_list_with_none():
    src = [1]
    pattern = None
    assert not is_match_tree(src, pattern)


def test_empty_lists_with_empty_pattern():
    src = []
    pattern = []
    assert is_match_tree(src, pattern)


def test_lists_with_empty_pattern():
    src = [1]
    pattern = []
    assert not is_match_tree(src, pattern)


def test_is_match_tree_between_list_and_other():
    src = [1]
    pattern = ast.Name('name')
    assert not is_match_tree(src, pattern)


def test_empty_lists_with_pattern():
    src = []
    pattern = [1]
    assert not is_match_tree(src, pattern)


def test_lists_with_list():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [1, 2, 3, 4, 5, 6]
    assert is_match_tree(src, pattern)


def test_lists_with_matcher():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "name"))]
    assert is_match_tree(src, pattern)


def test_lists_with_list_with_matcher_at_end():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [1, 2, PythonASTNode(ast.Name(MATCH_ALL + "name"))]
    assert is_match_tree(src, pattern, {})


def test_lists_with_list_with_matcher_at_start():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "name")), 5, 6]
    assert is_match_tree(src, pattern, {})


def test_lists_with_list_with_multi_single():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "name")), PythonASTNode(ast.Name(MATCH_ONE + "name"))]
    exp = {}
    assert is_match_tree(src, pattern, exp)
    assert exp["$$name"] == [1, 2, 3, 4, 5]
    assert exp["$name"] == [6]


def test_lists_with_list_with_list_multi_single():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [1, 2, PythonASTNode(ast.Name(MATCH_ALL + "name")), PythonASTNode(ast.Name(MATCH_ONE + "name"))]
    exp = {}
    assert is_match_tree(src, pattern, exp)
    assert exp["$$name"] == [3, 4, 5]
    assert exp["$name"] == [6]


def test_lists_with_list_with_matcher_in_the_middle():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [1, PythonASTNode(ast.Name(MATCH_ALL + "name")), 6]
    assert is_match_tree(src, pattern, {})


def test_lists_with_list_with_matcher_in_both_end():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "start")), 3, PythonASTNode(ast.Name(MATCH_ALL + "end"))]
    assert is_match_tree(src, pattern, {})


def test_lists_with_list_with_matcher_in_both_end_empty_list_at_start():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "start")), 1, PythonASTNode(ast.Name(MATCH_ALL + "end"))]
    assert is_match_tree(src, pattern, {})


def test_lists_with_list_with_matcher_in_both_end_empty_list_at_the_end():
    src = [1, 2, 3, 4, 5, 6]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "start")), 6, PythonASTNode(ast.Name(MATCH_ALL + "end"))]
    assert is_match_tree(src, pattern, {})


def test_lists_with_list_with_matcher_in_both_end__mismatch():
    src = [1, 2, 3, 4, 5, 61, 2, 3, 4, 5, 6]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "seq")), 6, PythonASTNode(ast.Name(MATCH_ALL + "seq"))]
    assert not is_match_tree(src, pattern, {})


def test_lists_with_list_with_matcher_in_both_end_same_pattern():
    src = [2, 3, 4, 5, 61, 2, 3, 4, 5]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "seq")), 61, PythonASTNode(ast.Name(MATCH_ALL + "seq"))]
    assert is_match_tree(src, pattern, {})


def test_lists_with_list_with_matcher_in_matcher_in_between():
    src = [2, 3, 4, 5, 61, 2, 3, 4, 5, 7, 8, 9]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "seq")), 61, PythonASTNode(ast.Name(MATCH_ALL + "seq")), 7, 8, 9]
    assert is_match_tree(src, pattern, {})


def test_lists_with_list_with_matcher_in_matcher_in_between_but_has_leftover():
    src = [2, 3, 4, 5, 61, 2, 3, 4, 5, 7, 8, 9]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "seq")), 61, PythonASTNode(ast.Name(MATCH_ALL + "seq"))]
    assert not is_match_tree(src, pattern, {})


def test_find_in_list():
    src = [2, 3, 4, 5, 61, 2, 3, 4, 5, 7, 8, 9]
    pattern = [2]
    assert find_in_list(src, pattern, {}) == 0


def test_find_in_list_with_expansion():
    src = [2, 3, 4, 5, 61, 2, 3, 4, 5, 7, 8, 9]
    pattern = [2, PythonASTNode(ast.Name(MATCH_ONE+'3')), 4]
    exp = {}
    assert find_in_list(src, pattern, exp) == 2
    assert exp['$3'] == [3]


def test_can_t_find_in_list():
    src = [2, 3, 4, 5, 61, 2, 3, 4, 5, 7, 8, 9]
    pattern = [1]
    assert find_in_list(src, pattern, {}) < 0


def test_find_in_list_returns_last_pos():
    src = [0, 1, 2, 3, 4, 5, 61, 2, 3, 4, 5, 7, 8, 9]
    pattern = [0, 1, 2, 3, 4, 5]
    assert find_in_list(src, pattern, {}) == 5


def test_find_with_match_all_returns_last_pos():
    src = [0, 1, 2, 3, 4, 5, 61, 2, 3, 4, 5, 7, 8, 9]
    pattern = [0, 1, 2, 3, 4, 5, PythonASTNode(ast.Name(MATCH_ALL + "seq"))]
    assert find_in_list(src, pattern, {}) == len(src) - 1


def test_lists_with_list_with_matcher_in_both_end_mismatch2():
    src = [1, 2, 3, 4, 5, 61, 2, 3, 4, 5, 6]
    pattern = [PythonASTNode(ast.Name(MATCH_ALL + "seq")), 6, PythonASTNode(ast.Name(MATCH_ALL + "seq"))]
    assert not is_match_tree(src, pattern, {})


def test_find_function_with_any_param_python():
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create_from_text('ca(13,14,15)', 'test.py')
    src = atu.children
    pattern_factory = PythonPatternFactory(factory, atu)
    pattern = pattern_factory.create_statements('ca($$all)')
    assert find_in_list(src, pattern, {}) == 0


def test_find_function_with_any_param_and_all_param_in_python():
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create_from_text('ca(13,14,15)', 'test.py')
    src = atu.children
    pattern_factory = PythonPatternFactory(factory, atu)
    pattern = pattern_factory.create_statements('$f($a,$$all)')
    assert find_in_list(src, pattern, {}) == 0


def test_match_all_function_with_any_param_clang():
    factory = ASTFactory(ClangASTNode, [])
    atu = factory.create_from_text('void ca(int a,int b,int c){ca(13,14,15); ca(13,14,15);}', 'fut.c')
    src = atu.children[-1].children[-1].children
    pattern_factory = CPatternFactory(factory)
    # atu = factory.create_from_text(, 'pat.c')
    pattern = \
    factory.create_from_text('int $a,$$all;void $f(int a,int b){$f($a, $$all);}', 'pat.c').children[-1].children[
        -1].children[0]
    assert len(MatchFinder.find_all(src, [pattern]).to_list()) == 2


def test_find_all_in_list_with_expansion():
    src = [2, 3, 4, 5, 61, 2, 3, 4, 5, 7, 8, 9]
    pattern = [2, PythonASTNode(ast.Name(MATCH_ONE+'3')), 4]
    exp = {}
    matches = MatchFinder.find_all(src, pattern).to_list()
    assert len(matches) == 2
    assert matches[0].expansions['$3'] == [3]

def test_find_all_in_python_list_with_expansion():
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create_from_text('''
from unittest import TestCase

class TestExample(TestCase):
    def test_case_example(self):
        # arrange
        factory = {}

        # act
        factory['a']= 1

        # assert
        self.assertEqual(len(factory), 1)
        ''', 'test_file.py')
    pattern_factory = PythonPatternFactory(factory, atu)
    pattern = pattern_factory.create_statements('class $name(TestCase):\n    $$cases')
    matches = MatchFinder.find_all(atu, pattern).to_list()
    assert len(matches) == 1
    assert matches[0].expansions['$name'] == ['TestExample']

def test_find_all_in_python_arg_list_with_expansion():
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create_from_text('class klass: pass', 'test_file.py')
    pattern_factory = PythonPatternFactory(factory, atu)
    statement = pattern_factory.create_statements('assertEqual(1,2,34,5,6,7,7,8)')
    pattern = pattern_factory.create_statements('assertEqual($$args)')
    matches = MatchFinder.find_all(statement, pattern).to_list()
    assert len(matches) == 1
    assert matches[0].expansions['$$args']

def test_find_all_in_python_arg_list_with_expansion():
    factory = ASTFactory(PythonASTNode, [])
    atu = factory.create_from_text('class klass:\n  def fun(a,b,c,d,f): pass', 'test_file.py')
    pattern_factory = PythonPatternFactory(factory, atu)
    pattern = pattern_factory.create_statements('def fun($$args): pass')
    matches = MatchFinder.find_all(atu, pattern).to_list()
    assert len(matches) == 1
    assert matches[0].expansions['$$args']

def test_find_all_in_clang_list_with_expansion():
    factory = ASTFactory(ClangASTNode, [])
    pattern = CPatternFactory(factory).create_statements('a == $x;')
    src = CPatternFactory(factory).create_statements('a == 3;a == 4; b == 5;')
    matches = MatchFinder.find_all(src, pattern).to_list()
    assert len(matches) == 2
    assert matches[0].expansions['$x']

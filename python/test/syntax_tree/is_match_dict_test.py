import ast
import unittest

import pytest

from impl.python import PythonASTNode, PythonPatternFactory
from impl.clang import ClangASTNode
from syntax_tree import ASTFactory, MatchFinder, CPatternFactory
from syntax_tree.ast_node import MATCH_ALL, MATCH_ONE
from syntax_tree.match_finder import is_match_tree, find_in_list, is_match_dict


def test_is_same_dict():
    src={ 'a': 'asd', 'b': 'zxc'}
    cmp={ 'a': 'asd', 'b': 'zxc'}
    assert is_match_dict(src,cmp,{})

def test_is_same_dict_different_key():
    src={ 'a': 'asd', 'b': 'zxc'}
    cmp={ 'a': 'asd', 'c': 'zxc'}
    assert not is_match_dict(src,cmp,{})

def test_is_same_dict_extra_key():
    src={ 'a': 'asd', 'b': 'zxc','extra': 'zxc'}
    cmp={ 'a': 'asd', 'b': 'zxc'}
    assert not is_match_dict(src,cmp,{})

def test_is_same_dict_missing_key():
    src={ 'a': 'asd', 'b': 'zxc'}
    cmp={ 'a': 'asd', 'b': 'zxc','extra': 'zxc'}
    assert not is_match_dict(src,cmp,{})

def test_is_same_dict_extra_irelevent_key():
    src={ 'a': 'asd', 'b': 'zxc','macro_expansion': 'zxc'}
    cmp={ 'a': 'asd', 'b': 'zxc',}
    assert is_match_dict(src,cmp,{})


def test_is_same_dict_key_in_expansion():
    src = {'a': 'asd', 'b': 'zxc', }
    cmp = {'a': 'asd', 'b': '$var', }
    assert is_match_dict(src, cmp, {'$var': ['zxc']})

def test_is_same_dict_key_no_expansion():
    src = {'a': 'asd', 'b': 'zxc', }
    cmp = {'a': 'asd', 'b': '$var', }
    assert is_match_dict(src, cmp, {})


def test_is_same_dict_key_in_expansion_with_different_value():
    src = {'a': 'asd', 'b': 'zxc', }
    cmp = {'a': 'asd', 'b': '$var', }
    assert not is_match_dict(src, cmp, {'$var': '_xc'})


def test_is_same_dict_key_in_expansion_in_src_should_not_happen():
    src={ 'a': 'asd', 'b': '$var',}
    cmp={ 'a': 'asd', 'b': 'zxc',}
    assert not is_match_dict(src,cmp,{})

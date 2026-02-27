import unittest

from renaissance.impl.clang import ClangASTNode
from renaissance.syntax_tree import CPatternFactory, ASTFactory


def test_find_all_in_clang_list_with_expansion():
    factory = ASTFactory(ClangASTNode, [])
    src = CPatternFactory(factory).create_statement('a == 3;')
    assert src.children[0].children[0].properties['name'] == 'a'

def test_marco_also_include_define():
    src = ClangASTNode.load_from_text('#define x "xxx"', 'test.c',[],None)
    assert len(src.children) ==1

def test_marco_also_include_define():
    src = ClangASTNode.load_from_text('#define x "xxx"', 'test.c',[],None)
    assert src.children[-1].signature == '#define x "xxx"'

def test_var_decl_includesemi_column():
    src = ClangASTNode.load_from_text('int x= 0;', 'test.c',[],None)
    assert src.children[-1].signature == 'int x= 0;'

@unittest.skip("last semicolumn is cut off")
def test_var_decl_include_semi_column_and_keep_space():
    src = ClangASTNode.load_from_text('   int    x   =    0   ;', 'test.c',[],None)
    assert src.children[-1].signature == '   int    x   =    0   ;'

def test_struct_include_semicolumn():
    src = ClangASTNode.load_from_text('struct s;', 'test.c',[],None)
    assert src.children[-1].signature == 'struct s;'

@unittest.skip("last semicolumn is cut off")
def test_struct_include_semicolumn_and_space():
    src = ClangASTNode.load_from_text('struct s{intx, int y\n} ;', 'test.c',[],None)
    assert src.children[-1].signature == 'struct s{intx, int y\n} ;'

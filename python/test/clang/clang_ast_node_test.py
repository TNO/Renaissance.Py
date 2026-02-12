

from impl.clang import ClangASTNode
from syntax_tree import ASTShower, CPatternFactory, ASTFactory


def test_find_all_in_clang_list_with_expansion():
    factory = ASTFactory(ClangASTNode, [])
    src = CPatternFactory(factory).create_statement('a == 3;')
    assert src.children[0].children[0].properties['name'] == 'a'

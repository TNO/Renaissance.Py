

from renaissance.impl.clang import ClangASTNode
from renaissance.syntax_tree import CPatternFactory, ASTFactory


def test_find_all_in_clang_list_with_expansion():
    factory = ASTFactory(ClangASTNode, [])
    src = CPatternFactory(factory).create_statement('a == 3;')
    assert src.children[0].children[0].properties['name'] == 'a'

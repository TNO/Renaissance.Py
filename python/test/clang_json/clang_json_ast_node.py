from impl.clang_json import ClangJsonASTNode
from syntax_tree import ASTShower, CPatternFactory, ASTFactory


def test_find_all_in_clang_list_with_expansion():
    factory = ASTFactory(ClangJsonASTNode, [])
    src = CPatternFactory(factory).create_statement('a == 3;')
    ASTShower.show_node(src, True)
    # assert src.children[0].children[0].properties['name'] == 'a'

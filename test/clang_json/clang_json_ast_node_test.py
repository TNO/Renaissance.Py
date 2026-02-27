from renaissance.impl.clang_json import ClangJsonASTNode
from renaissance.syntax_tree import ASTShower, CPatternFactory, ASTFactory
import unittest


def test_dump_json_form_clang_lib():
    # TranslationUnit.from_source(file_name, unsaved_files,args)
    #use clang natie lib t6o dump json
    pass
def test_load_from_text():
    node = ClangJsonASTNode.load_from_text("int main(){return 0;}", "hello.c", [],"")
    assert isinstance(node, ClangJsonASTNode)

def test_find_all_in_clang_list_with_expansion():
    factory = ASTFactory(ClangJsonASTNode, [])
    src = CPatternFactory(factory).create_statement('a == 3;')
    ASTShower.show_node(src, True)
    # assert src.children[0].children[0].properties['name'] == 'a'

if __name__ == "__main__":
    unittest.main()

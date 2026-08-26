from pathlib import Path

import pytest
from hamcrest import *

from renaissance.impl.clang import CPatternFactory
from renaissance.impl.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.syntax_tree import ASTFactory, ASTShower

pytest.mark.skip("empty workdir should also work right?")


class TestClangJsonAstNode:
    def test_load_from_text_empty_dir(self):
        node = ClangJsonASTNode.load_from_text("int main(){return 0;}", "hello.c", [], Path(""))
        assert_that(isinstance(node, ClangJsonASTNode))

    def test_load_from_text(self):
        node = ClangJsonASTNode.load_from_text("int main(){return 0;}", "hello.c", [], Path("."))
        assert_that(isinstance(node, ClangJsonASTNode))

    def test_name_in_props(self):
        factory = ASTFactory(ClangJsonASTNode, [])
        src = CPatternFactory(factory).create_statement("a == 3;")
        ASTShower.show_node(src, True)
        assert_that(src.children[0].properties["name"], is_("a"))


if __name__ == "__main__":
    pytest.main()

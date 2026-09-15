from pathlib import Path

import pytest
from hamcrest import assert_that, is_

from renaissance.integrations.clang import CPatternFactory
from renaissance.integrations.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.syntax_tree import ASTFactory, ASTShower

pytest.mark.skip("empty workdir should also work right?")


class TestClangJsonAstNode:
    def test_load_from_text_empty_dir(self):
        node = ClangJsonASTNode.load_from_text("int main(){return 0;}", "hello.c", [], Path())
        assert_that(isinstance(node, ClangJsonASTNode))

    def test_load_from_text(self):
        node = ClangJsonASTNode.load_from_text("int main(){return 0;}", "hello.c", [], Path())
        assert_that(isinstance(node, ClangJsonASTNode))

    def test_name_in_props(self):
        factory = ASTFactory(ClangJsonASTNode, [])
        src = CPatternFactory(factory).create_statement("a == 3;")
        ASTShower.show_node(src, True)
        assert_that(src.children[0].properties["name"], is_("a"))

    @pytest.mark.xfail(
        reason="ClangJsonASTNode defines __eq__ but not __hash__, so Python implicitly sets "
        "__hash__ = None - instances are unhashable, unlike the sibling ClangASTNode class, "
        "which defines both.",
        strict=True,
    )
    def test_is_hashable(self):
        node = ClangJsonASTNode.load_from_text("int main(){return 0;}", "hello.c", [], Path())
        hash(node)


if __name__ == "__main__":
    pytest.main()

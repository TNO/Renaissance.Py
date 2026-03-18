from pathlib import Path

from renaissance.impl.clang_json import ClangJsonASTNode
from renaissance.impl.clang import CPatternFactory
from renaissance.syntax_tree import ASTShower, ASTFactory
import pytest
from hamcrest import *

pytest.mark.skip("empty workdir should also work right?")


def test_load_from_text_empty_dir():
    node = ClangJsonASTNode.load_from_text("int main(){return 0;}", "hello.c", [], Path(""))
    assert_that(isinstance(node, ClangJsonASTNode))


def test_load_from_text():
    node = ClangJsonASTNode.load_from_text("int main(){return 0;}", "hello.c", [], Path("."))
    assert_that(isinstance(node, ClangJsonASTNode))


def test_name_in_props():
    factory = ASTFactory(ClangJsonASTNode, [])
    src = CPatternFactory(factory).create_statement('a == 3;')
    ASTShower.show_node(src, True)
    assert_that(src.children[0].properties['name'], is_('a'))


if __name__ == "__main__":
    pytest.main()

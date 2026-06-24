
from hamcrest import assert_that, is_

from renaissance.impl.clang import ClangASTNode
from renaissance.syntax_tree import ASTProcessor, ASTFactory, PatternMatch


class TestAstProcessor:
    def test_find_match(self, mocker):
        node = mocker.Mock()
        pattern_match = PatternMatch([node, node, node], {}, [])
        mock_matcher = mocker.patch(
            "renaissance.syntax_tree.match_finder.find_all",
            return_value=[pattern_match],
        )
        atu = ClangASTNode.load_from_text("int main(){return 0;}", "test.c", [], None)
        ast_refactor = ASTProcessor(atu, ASTFactory(ClangASTNode), in_memory=True)

        ast_refactor.find_match([atu.children[-1].children[-1]])

        assert_that(mock_matcher.call_count, is_(1))

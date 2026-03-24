from hamcrest import assert_that, is_, contains_exactly, has_length

from renaissance.syntax_tree import PatternMatch, MatchFinder, ASTShower
from renaissance.syntax_tree.match_finder import is_match


class TestPatternMatch:
    def test_match_referenced_by(self, mocker):
        node = mocker.Mock()
        reference = mocker.Mock()
        node.referenced_by = [reference, reference]
        reference.node = node
        pattern_match = PatternMatch([node, node, node], {}, [])
        mock_matcher = mocker.patch(
            "renaissance.syntax_tree.match_finder.MatchFinder.match_pattern",
            return_value=[pattern_match],
        )
        pattern_match.match_referenced_by([[node]], False)
        assert_that(mock_matcher.call_count, is_(6))

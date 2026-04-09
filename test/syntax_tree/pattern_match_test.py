import ast

from hamcrest import assert_that, is_

from renaissance.impl.python import PythonRstNode
from renaissance.syntax_tree import PatternMatch


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

    def test_get_key_redirect_to_expansion_signature(self, mocker):
        node = mocker.Mock()
        node.signature = "name_1"
        pattern_match = PatternMatch([], {"key": ["name_1"], "$node": [PythonRstNode(ast.Name("node_name"))], "empty": []}, "patterns")
        assert_that(pattern_match["key"], is_("name_1"))
        assert_that(pattern_match["$node"], is_("node_name"))
        assert_that(pattern_match["empty"], is_(""))

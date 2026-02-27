
from renaissance.syntax_tree import PatternMatch, MatchFinder


def test_match_referenced_by(mocker):
    node = mocker.Mock()
    reference = mocker.Mock()
    node.references = [reference]
    reference.node = node
    pattern_match = PatternMatch([node], {}, [])
    mocker.patch("syntax_tree.match_finder.MatchFinder.match_pattern", return_value=[pattern_match])
    pattern_match.match_references([[node]], False)
    MatchFinder.match_pattern.assert_called_once_with([node], [node], False)


def test_match_referenced_by(mocker):
    node = mocker.Mock()
    reference = mocker.Mock()
    node.referenced_by = [reference, reference]
    reference.node = node
    pattern_match = PatternMatch([node, node, node], {}, [])
    mock_matcher = mocker.patch("syntax_tree.match_finder.MatchFinder.match_pattern", return_value=[pattern_match])
    pattern_match.match_referenced_by([[node]], False)
    assert mock_matcher.call_count == 6

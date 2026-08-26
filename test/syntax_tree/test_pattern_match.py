import ast
import textwrap

import pytest
from hamcrest import assert_that, empty, has_length, is_

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.syntax_tree import PatternMatch
from renaissance.syntax_tree.match_finder import match_pattern


class TestPatternMatch:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.pattern_factory = PythonPatternFactory(self.factory)

    @pytest.mark.skip("length on empty node")
    def test_empty_expansion_has_offset(self):
        example_code = textwrap.dedent("""
        1
        2
        3
        4
        5
        6
        7
                """)
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("2\n\n$$empty\n3")
        found = match_pattern(atu.children, pattern)
        assert_that(found, has_length(1))
        match = found[0]
        assert_that(match["$$empty"], is_(""))
        assert_that(match.expansions["$$empty"], is_(empty()))
        assert_that(match.offset_of("$$empty"), is_(5))
        assert_that(match.length_of("$$empty"), is_(0))

    def test_single_expansion_has_offset(self):
        example_code = textwrap.dedent("""
        1
        2
        3
        4
        5
        6
        7
                """)
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("2\n\n$3\n4")
        found = match_pattern(atu.children, pattern)
        assert_that(found, has_length(1))
        match = found[0]
        assert_that(match["$3"], is_("3"))
        assert_that(match.expansions["$3"], has_length(1))
        assert_that(match.offset_of("$3"), is_(5))
        assert_that(match.length_of("$3"), is_(1))

    def test_multi_expansion_has_offset(self):
        example_code = textwrap.dedent("""
        1
        2
        3
        4
        5
        6
        7
                """)
        atu = self.factory.create_from_text(example_code)
        pattern = self.pattern_factory.create_statements("1\n\n$$other\n6")
        found = match_pattern(atu.children, pattern)
        assert_that(found, has_length(1))
        match = found[0]
        assert_that(match["$$other"], is_("2\n3\n4\n5"))
        assert_that(match.expansions["$$other"], has_length(4))
        assert_that(match.offset_of("$$other"), is_(3))
        assert_that(match.length_of("$$other"), is_(7))

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

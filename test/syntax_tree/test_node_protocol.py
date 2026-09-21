"""Tests that arbitrary structural nodes satisfy the NodeProtocol."""

from renaissance.syntax_tree.match_finder import is_match
from renaissance.syntax_tree.node_protocol import NodeProtocol
from renaissance.syntax_tree.semantic_kind import SemanticKind


class FakeNode:
    """AI: Minimal test double satisfying NodeProtocol via duck typing."""

    parser_kind = "fake_node"
    semantic_kind = SemanticKind.NODE
    properties = {}
    children = []
    signature = "fake"
    name = ""


def test_structural_node_satisfies_protocol():
    """AI: Assert a duck-typed structural node satisfies NodeProtocol via isinstance."""
    assert isinstance(FakeNode(), NodeProtocol)


def test_matcher_prefers_semantic_kind_over_legacy_type():
    """AI: Assert is_match prefers matching by semantic_kind over the legacy parser_kind field."""
    source = FakeNode()
    pattern = FakeNode()
    source.semantic_kind = SemanticKind.CALL
    pattern.semantic_kind = SemanticKind.CALL
    source.parser_kind = "source_node"
    pattern.parser_kind = "pattern_node"

    assert is_match(source, pattern)

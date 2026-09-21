"""Tests for the PatternKind enum values."""

from renaissance.syntax_tree.pattern_kind import PatternKind


def test_pattern_kind_values_are_distinct():
    """AI: Assert distinct PatternKind enum members compare unequal."""
    assert PatternKind.MATCH_ONE != PatternKind.MATCH_ALL

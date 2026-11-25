# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the PatternKind enum values."""

from renaissance.core.pattern import PatternKind


def test_pattern_kind_values_are_distinct() -> None:
    """AI: Assert distinct PatternKind enum members compare unequal."""
    assert PatternKind.MATCH_ONE != PatternKind.MATCH_ALL

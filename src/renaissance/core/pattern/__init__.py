# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The pattern language: the placeholders in a pattern and the kinds of pattern matching."""

from renaissance.core.pattern.pattern_kind import PatternKind
from renaissance.core.pattern.placeholders import MATCH_ALL, MATCH_ONE, detect_placeholder, replace_dollar, use_dollar

__all__ = [
    "MATCH_ALL",
    "MATCH_ONE",
    "PatternKind",
    "detect_placeholder",
    "replace_dollar",
    "use_dollar",
]

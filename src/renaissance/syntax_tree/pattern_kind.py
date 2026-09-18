"""AI: Enumeration of pattern-matching modes (match-one vs. match-all)."""

from enum import StrEnum


class PatternKind(StrEnum):
    """AI: Enumerate the pattern-matching modes (match-one vs. match-all)."""

    MATCH_ONE = "match_one"
    MATCH_ALL = "match_all"

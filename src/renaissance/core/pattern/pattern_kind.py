# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Enumeration of pattern-matching modes (match-one vs. match-all)."""

from enum import StrEnum


class PatternKind(StrEnum):
    """AI: Enumerate the pattern-matching modes (match-one vs. match-all)."""

    MATCH_ONE = "match_one"
    MATCH_ALL = "match_all"

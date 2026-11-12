# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The node equality helpers, with which parser bindings implement __eq__."""

from collections.abc import Set as AbstractSet


def match_props(mine, other, irrelevant_props: AbstractSet[str]) -> bool:
    """AI: Return True if mine and other agree on all properties except the irrelevant ones."""
    all_keys = (mine.keys() | other.keys()) - irrelevant_props
    return all(mine.get(n) == other.get(n) for n in all_keys)


def match_children(mine, other, irrelevant_kinds: AbstractSet[str]) -> bool:
    """AI: Return True if every child in other matches the corresponding child in mine (or has an irrelevant kind)."""
    if mine is None or other is None:
        return mine == other
    # TODO(pjljvandelaar): asymmetric - extra trailing children of mine are ignored, so a == b need not imply b == a.
    #  https://github.com/TNO/Renaissance.Py/issues/187
    return all((i < len(mine) and mine[i] == child) or child.parser_kind in irrelevant_kinds for i, child in enumerate(other))

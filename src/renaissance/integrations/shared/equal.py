# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The node equality helpers, with which parser bindings implement __eq__."""

from collections.abc import Callable, Mapping, Sequence


def equal_in_properties(mine: Mapping[str, object], other: Mapping[str, object], is_relevant_property: Callable[[str], bool]) -> bool:
    """Return whether mine and other have the same relevant properties with equal values."""
    return {n: v for n, v in mine.items() if is_relevant_property(n)} == {n: v for n, v in other.items() if is_relevant_property(n)}


def equal_in_children[T](mine: Sequence[T], other: Sequence[T], is_relevant_child: Callable[[T], bool]) -> bool:
    """Return whether mine and other have the same relevant children in the same order."""
    return [c for c in mine if is_relevant_child(c)] == [c for c in other if is_relevant_child(c)]

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the node equality helpers equal_in_properties and equal_in_children."""

from hamcrest import assert_that, equal_to, is_
from hypothesis import given
from hypothesis import strategies as st

from renaissance.integrations.shared import equal_in_children, equal_in_properties


def is_relevant_property(name: str) -> bool:
    """Treat the properties whose name starts with an underscore as irrelevant."""
    return not name.startswith("_")


def is_relevant_child(child: str) -> bool:
    """Treat the children that start with # as irrelevant, as comments."""
    return not child.startswith("#")


relevant_names = st.text(alphabet="abc", min_size=1, max_size=2)
irrelevant_names = relevant_names.map(lambda name: "_" + name)
values = st.one_of(st.none(), st.integers(min_value=0, max_value=2))
relevant_children = st.text(alphabet="ab", min_size=1, max_size=2)
irrelevant_children = relevant_children.map(lambda child: "#" + child)
children = st.lists(st.one_of(relevant_children, irrelevant_children), max_size=5)


def without_irrelevant(sequence: list[str]) -> list[str]:
    """Return the relevant children of sequence."""
    return [c for c in sequence if is_relevant_child(c)]


# equal_in_properties


def test_properties_both_empty() -> None:
    """Two mappings without properties are equal."""
    assert_that(equal_in_properties({}, {}, is_relevant_property), is_(True))


def test_properties_same() -> None:
    """Two mappings with the same properties are equal."""
    assert_that(equal_in_properties({"a": 1, "b": "x"}, {"b": "x", "a": 1}, is_relevant_property), is_(True))


def test_properties_relevant_value_differs() -> None:
    """A relevant property with different values makes the mappings unequal."""
    assert_that(equal_in_properties({"a": 1}, {"a": 2}, is_relevant_property), is_(False))


def test_properties_irrelevant_value_differs() -> None:
    """An irrelevant property with different values is ignored."""
    assert_that(equal_in_properties({"a": 1, "_c": 1}, {"a": 1, "_c": 2}, is_relevant_property), is_(True))


def test_properties_relevant_property_only_in_mine() -> None:
    """A relevant property that only mine has makes the mappings unequal."""
    assert_that(equal_in_properties({"a": 1, "b": 2}, {"a": 1}, is_relevant_property), is_(False))


def test_properties_relevant_property_only_in_other() -> None:
    """A relevant property that only other has makes the mappings unequal."""
    assert_that(equal_in_properties({"a": 1}, {"a": 1, "b": 2}, is_relevant_property), is_(False))


def test_properties_irrelevant_property_only_in_one() -> None:
    """An irrelevant property that only one mapping has is ignored."""
    assert_that(equal_in_properties({"a": 1, "_c": 1}, {"a": 1}, is_relevant_property), is_(True))
    assert_that(equal_in_properties({"a": 1}, {"a": 1, "_c": 1}, is_relevant_property), is_(True))


def test_properties_missing_differs_from_none() -> None:
    """A missing property differs from a property with value None."""
    assert_that(equal_in_properties({"a": None}, {}, is_relevant_property), is_(False))
    assert_that(equal_in_properties({}, {"a": None}, is_relevant_property), is_(False))


def test_properties_nothing_relevant() -> None:
    """When no property is relevant, all mappings are equal."""
    assert_that(equal_in_properties({"a": 1}, {"b": 2}, lambda _: False), is_(True))


def test_properties_values_compared_with_eq() -> None:
    """Values are compared with ==, not with identity."""
    assert_that(equal_in_properties({"a": [1, 2]}, {"a": [1, 2]}, is_relevant_property), is_(True))


@given(st.dictionaries(st.one_of(relevant_names, irrelevant_names), values))
def test_properties_reflexive(mine: dict[str, int | None]) -> None:
    """Every mapping equals itself."""
    assert_that(equal_in_properties(mine, dict(mine), is_relevant_property), is_(True))


@given(
    st.dictionaries(st.one_of(relevant_names, irrelevant_names), values),
    st.dictionaries(st.one_of(relevant_names, irrelevant_names), values),
)
def test_properties_symmetric(mine: dict[str, int | None], other: dict[str, int | None]) -> None:
    """The order of the arguments does not matter."""
    assert_that(
        equal_in_properties(mine, other, is_relevant_property),
        equal_to(equal_in_properties(other, mine, is_relevant_property)),
    )


@given(
    st.dictionaries(st.one_of(relevant_names, irrelevant_names), values),
    st.dictionaries(st.one_of(relevant_names, irrelevant_names), values),
)
def test_properties_equal_relevant_parts(mine: dict[str, int | None], other: dict[str, int | None]) -> None:
    """The mappings are equal exactly when their relevant parts are equal."""
    relevant_mine = {name: value for name, value in mine.items() if is_relevant_property(name)}
    relevant_other = {name: value for name, value in other.items() if is_relevant_property(name)}
    assert_that(equal_in_properties(mine, other, is_relevant_property), equal_to(relevant_mine == relevant_other))


# equal_in_children


def test_children_both_empty() -> None:
    """Two empty lists of children are equal."""
    assert_that(equal_in_children([], [], is_relevant_child), is_(True))


def test_children_same() -> None:
    """Two lists with the same children are equal."""
    assert_that(equal_in_children(["a", "b"], ["a", "b"], is_relevant_child), is_(True))


def test_children_relevant_child_differs() -> None:
    """A relevant child that differs makes the lists unequal."""
    assert_that(equal_in_children(["a", "b"], ["a", "c"], is_relevant_child), is_(False))


def test_children_order_matters() -> None:
    """The same children in another order make the lists unequal."""
    assert_that(equal_in_children(["a", "b"], ["b", "a"], is_relevant_child), is_(False))


def test_children_only_irrelevant() -> None:
    """Lists with only irrelevant children equal the empty list."""
    assert_that(equal_in_children(["#x", "#y"], [], is_relevant_child), is_(True))


def test_children_nothing_relevant() -> None:
    """When no child is relevant, all lists are equal."""
    assert_that(equal_in_children(["a"], ["b", "c"], lambda _: False), is_(True))


def test_children_extra_trailing_child_in_mine() -> None:
    """Regression: an extra trailing child of mine was ignored, so a == b did not imply b == a."""
    assert_that(equal_in_children(["a", "b"], ["a"], is_relevant_child), is_(False))
    assert_that(equal_in_children(["a"], ["a", "b"], is_relevant_child), is_(False))


def test_children_irrelevant_child_in_mine() -> None:
    """Regression: an irrelevant child of mine was compared, as only the children of other were checked."""
    assert_that(equal_in_children(["#x", "a"], ["a"], is_relevant_child), is_(True))


def test_children_irrelevant_child_in_other() -> None:
    """Regression: an irrelevant child of other shifted the comparison of the children after it."""
    assert_that(equal_in_children(["a"], ["#x", "a"], is_relevant_child), is_(True))


def test_children_irrelevant_children_at_different_positions() -> None:
    """Irrelevant children are ignored, whatever their number and position."""
    assert_that(equal_in_children(["#x", "a", "b"], ["a", "#y", "#z", "b", "#w"], is_relevant_child), is_(True))


@given(children)
def test_children_reflexive(mine: list[str]) -> None:
    """Every list of children equals itself."""
    assert_that(equal_in_children(mine, list(mine), is_relevant_child), is_(True))


@given(children, children)
def test_children_symmetric(mine: list[str], other: list[str]) -> None:
    """The order of the arguments does not matter."""
    assert_that(
        equal_in_children(mine, other, is_relevant_child),
        equal_to(equal_in_children(other, mine, is_relevant_child)),
    )


@given(children, children)
def test_children_equal_relevant_children(mine: list[str], other: list[str]) -> None:
    """The lists are equal exactly when their relevant children are equal, in the same order."""
    assert_that(
        equal_in_children(mine, other, is_relevant_child),
        equal_to(without_irrelevant(mine) == without_irrelevant(other)),
    )


@given(children, st.lists(st.tuples(st.integers(min_value=0), irrelevant_children), max_size=3))
def test_children_inserted_irrelevant_children(mine: list[str], insertions: list[tuple[int, str]]) -> None:
    """Inserting irrelevant children anywhere keeps the lists equal."""
    other = list(mine)
    for position, child in insertions:
        other.insert(position % (len(other) + 1), child)
    assert_that(equal_in_children(mine, other, is_relevant_child), is_(True))

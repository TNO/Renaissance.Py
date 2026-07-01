"""
Step implementations for features/rewrite-semantics.feature.

Scenarios 1, 2, and 4 are marked xfail because the corresponding behaviour is
not yet fully implemented:
  - Scenario 1: covered-change filtering is disabled in _RewriteActions
    (``__is_ancestor_in_nodes`` always returns False).
  - Scenario 2: the Rewriter merges overlapping rewrites instead of raising.
  - Scenario 4: append ordering (descendant before ancestor) is not yet enforced.

Scenario 0 (Replacements of the same node produce an error) uses a Scenario
Outline for representative examples. The universal property test is in:
  test/syntax_tree/test_rewrite_semantics_properties.py
"""

from __future__ import annotations

import pytest
from pytest_bdd import given, when, then, scenario, parsers

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.syntax_tree import ASTRewriter
from renaissance.syntax_tree.match_finder import match_pattern

_FEATURE = "../rewrite-semantics.feature"


# ── Scenario functions ────────────────────────────────────────────────────────

# Scenario 0 — Scenario Outline: three representative examples.
# Universal property test: test/syntax_tree/test_rewrite_semantics_properties.py
@pytest.mark.xfail(
    reason="Replacing the same node twice is not yet rejected by ASTRewriter",
    strict=True,
)
@scenario(_FEATURE, "Replacements of the same node produce an error")
def test_replacements_of_same_node_produce_error():
    pass


@pytest.mark.xfail(
    reason="Covered-change filtering not yet active: _RewriteActions.__is_ancestor_in_nodes always returns False",
    strict=True,
)
@scenario(_FEATURE, "Covered changes are not applied")
def test_covered_changes_not_applied():
    pass


@pytest.mark.xfail(
    reason="Overlapping replacement detection not yet implemented: Rewriter merges instead of raising",
    strict=True,
)
@scenario(_FEATURE, "Overlapping replacements produce an error")
def test_overlapping_replacements_produce_error():
    pass


@scenario(_FEATURE, "Prepend of ancestor precedes prepend of descendant at the same text location")
def test_prepend_ordering():
    pass


@pytest.mark.xfail(
    reason="Append ordering (descendant before ancestor) not yet enforced: Rewriter appends in insertion order",
    strict=True,
)
@scenario(_FEATURE, "Append of descendant precedes append of ancestor at the same text location")
def test_append_ordering():
    pass


@scenario(_FEATURE, "Append of sibling precedes prepend of next consecutive sibling")
def test_sibling_append_prepend_ordering():
    pass


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture
def context() -> dict:
    return {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _first_leaf(node: PythonRstNode) -> PythonRstNode:
    """Return the leftmost leaf descendant of *node*."""
    current = node
    while current.children:
        current = current.children[0]
    return current


def _last_leaf(node: PythonRstNode) -> PythonRstNode:
    """Return the rightmost leaf descendant of *node*."""
    current = node
    while current.children:
        current = current.children[-1]
    return current


def _find_statement(atu: PythonRstNode, factory: PythonFactory, text: str) -> PythonRstNode:
    """Return the first top-level statement whose source text matches *text*."""
    pattern_factory = PythonPatternFactory(factory)
    pattern = pattern_factory.create_statements(text)
    matches = match_pattern(atu.children, pattern)
    assert matches, f"No statement matching {text!r} found in source"
    return matches[0].nodes[0]


# ── Given steps ───────────────────────────────────────────────────────────────

@given("a Python language factory")
def given_python_factory(context: dict) -> None:
    context["factory"] = PythonFactory(PythonRstNode)


@given(parsers.parse("the source '{source}'"))
def given_source(context: dict, source: str) -> None:
    source = source.replace("\\n", "\n")
    context["source"] = source
    factory: PythonFactory = context["factory"]
    context["atu"] = factory.create_from_text(source, "test.py")
    context["rewriter"] = ASTRewriter(context["atu"])


# ── Node-selection Given steps ────────────────────────────────────────────────

@given(parsers.parse("the statement '{text}' is a node"))
def given_statement_as_node(context: dict, text: str) -> None:
    context["node"] = _find_statement(context["atu"], context["factory"], text)


@given(parsers.parse("the statement '{text}' is the parent node"))
def given_statement_as_parent(context: dict, text: str) -> None:
    context["parent"] = _find_statement(context["atu"], context["factory"], text)


@given("the first leaf of the parent is the child node")
def given_first_leaf_of_parent_as_child(context: dict) -> None:
    context["child"] = _first_leaf(context["parent"])


@given(parsers.parse("the statement '{text}' is the ancestor node"))
def given_statement_as_ancestor(context: dict, text: str) -> None:
    context["ancestor"] = _find_statement(context["atu"], context["factory"], text)


@given("the first leaf of the ancestor is the descendant node")
def given_first_leaf_as_descendant(context: dict) -> None:
    context["descendant"] = _first_leaf(context["ancestor"])


@given("the last leaf of the ancestor is the descendant node")
def given_last_leaf_as_descendant(context: dict) -> None:
    context["descendant"] = _last_leaf(context["ancestor"])


@given(parsers.parse("the statement '{text}' is the first sibling"))
def given_first_sibling(context: dict, text: str) -> None:
    context["sibling1"] = _find_statement(context["atu"], context["factory"], text)


@given(parsers.parse("the statement '{text}' is the second sibling"))
def given_second_sibling(context: dict, text: str) -> None:
    context["sibling2"] = _find_statement(context["atu"], context["factory"], text)


@given(parsers.parse("the statement '{text}' is the third sibling"))
def given_third_sibling(context: dict, text: str) -> None:
    context["sibling3"] = _find_statement(context["atu"], context["factory"], text)


# ── When steps ────────────────────────────────────────────────────────────────

@when(parsers.parse("the node is replaced with '{text}'"))
def when_replace_node(context: dict, text: str) -> None:
    context["rewriter"].replace(text, [context["node"]])


@when(parsers.parse("the parent node is replaced with '{text}'"))
def when_replace_parent(context: dict, text: str) -> None:
    context["rewriter"].replace(text, [context["parent"]])


@when(parsers.parse("the child node is prepended with '{text}'"))
def when_prepend_child(context: dict, text: str) -> None:
    context["rewriter"].insert_before(text, [context["child"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the first and second siblings are replaced with '{text}'"))
def when_replace_first_second(context: dict, text: str) -> None:
    context["rewriter"].replace(text, [context["sibling1"], context["sibling2"]])


@when(parsers.parse("the second and third siblings are replaced with '{text}'"))
def when_replace_second_third(context: dict, text: str) -> None:
    context["rewriter"].replace(text, [context["sibling2"], context["sibling3"]])


@when(parsers.parse("the ancestor is prepended with '{text}'"))
def when_prepend_ancestor(context: dict, text: str) -> None:
    context["rewriter"].insert_before(text, [context["ancestor"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the descendant is prepended with '{text}'"))
def when_prepend_descendant(context: dict, text: str) -> None:
    context["rewriter"].insert_before(text, [context["descendant"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the ancestor is appended with '{text}'"))
def when_append_ancestor(context: dict, text: str) -> None:
    context["rewriter"].insert_after(text, [context["ancestor"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the descendant is appended with '{text}'"))
def when_append_descendant(context: dict, text: str) -> None:
    context["rewriter"].insert_after(text, [context["descendant"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the first sibling is appended with '{text}'"))
def when_append_first_sibling(context: dict, text: str) -> None:
    context["rewriter"].insert_after(text, [context["sibling1"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the second sibling is prepended with '{text}'"))
def when_prepend_second_sibling(context: dict, text: str) -> None:
    context["rewriter"].insert_before(text, [context["sibling2"]], include_whitespace=False, include_comments=False)


# ── Then steps ────────────────────────────────────────────────────────────────

@then("applying the changes raises an error")
def then_applying_raises_error(context: dict) -> None:
    with pytest.raises(Exception):
        context["rewriter"].apply_to_string()


@then(parsers.parse("the result contains '{text}'"))
def then_result_contains(context: dict, text: str) -> None:
    result = context["rewriter"].apply_to_string()
    assert text in result, f"Expected {text!r} in result, got: {result!r}"


@then(parsers.parse("the result does not contain '{text}'"))
def then_result_not_contains(context: dict, text: str) -> None:
    result = context["rewriter"].apply_to_string()
    assert text not in result, f"Did not expect {text!r} in result, got: {result!r}"


@then(parsers.parse("'{a}' appears before '{b}' in the result"))
def then_a_before_b(context: dict, a: str, b: str) -> None:
    result = context["rewriter"].apply_to_string()
    pos_a = result.find(a)
    pos_b = result.find(b)
    assert pos_a != -1, f"Expected {a!r} in result, got: {result!r}"
    assert pos_b != -1, f"Expected {b!r} in result, got: {result!r}"
    assert pos_a < pos_b, (
        f"Expected {a!r} (at {pos_a}) to appear before {b!r} (at {pos_b}) in result: {result!r}"
    )

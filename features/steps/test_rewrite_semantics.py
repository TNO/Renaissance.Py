"""Step implementations for features/rewrite_semantics.feature.

Scenarios 1 and 2 are marked xfail because the corresponding behaviour is not
yet fully implemented:
  - Scenario 1: dominated-change filtering is disabled in _RewriteActions
    (``__is_ancestor_in_nodes`` always returns False).
  - Scenario 2: the Rewriter merges overlapping rewrites instead of raising.

The prepend/append ordering scenarios each fail for only ONE collection
order (the Rewriter orders insertions by collection order, not AST
structure, so the other order passes by coincidence). The failing Example
row of each is tagged in the .feature file (``@xfail_prepend_descendant_first``,
``@xfail_append_ancestor_first``) and converted to a strict xfail marker by
the ``pytest_bdd_apply_tag`` hook in conftest.py, so the passing collection
order stays a real, non-xfail test.

Scenario 0 (Replacements of the same node produce an error) uses a Scenario
Outline for representative examples. The universal property test is in:
  test/syntax_tree/test_rewrite_semantics_properties.py
"""

from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from renaissance.integrations.clang import ClangASTNode, CPPPatternFactory
from renaissance.integrations.clang.predicates import is_clang_compound_statement
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree import ASTFactory, ASTRewriter
from renaissance.syntax_tree.ast_finder import find_nodes
from renaissance.syntax_tree.match_finder import match_pattern

_FEATURE = "../rewrite-semantics.feature"


# ── Scenario functions ────────────────────────────────────────────────────────


# Scenario 0 — Scenario Outline: three representative examples.
# Universal property test: test/syntax_tree/test_rewrite_semantics_properties.py
@scenario(_FEATURE, "Replacements of the same node produce an error")
def test_replacements_of_same_node_produce_error():
    """AI: Scenario test for 'Replacements of the same node produce an error'."""


@pytest.mark.xfail(
    reason="Dominated-change filtering not yet active: _RewriteActions.__is_ancestor_in_nodes always returns False",
    strict=True,
)
@scenario(_FEATURE, "Dominated change is not applied")
def test_dominated_change_not_applied():
    """AI: Scenario test for 'Dominated change is not applied'."""


@scenario(_FEATURE, "Overlapping replacements produce an error")
def test_overlapping_replacements_produce_error():
    """AI: Scenario test for 'Overlapping replacements produce an error'."""


@scenario(_FEATURE, "Prepend of ancestor precedes prepend of descendant regardless of collection order")
def test_prepend_ordering():
    """AI: Scenario test for 'Prepend of ancestor precedes prepend of descendant regardless of collection order'."""


@scenario(_FEATURE, "Append of descendant precedes append of ancestor regardless of collection order")
def test_append_ordering():
    """AI: Scenario test for 'Append of descendant precedes append of ancestor regardless of collection order'."""


@scenario(_FEATURE, "Operation on first sibling precedes operation on second sibling \u2014 first sibling collected first")
def test_sibling_sib1_first():
    """AI: Scenario test for 'Operation on first sibling precedes operation on second sibling' (first sibling collected first)."""


@scenario(_FEATURE, "Operation on first sibling precedes operation on second sibling \u2014 second sibling collected first")
def test_sibling_sib2_first():
    """AI: Scenario test for 'Operation on first sibling precedes operation on second sibling' (second sibling collected first)."""


@scenario(_FEATURE, "Replacements of the same sibling range produce an error")
def test_replacements_of_same_sibling_range_produce_error():
    """AI: Scenario test for 'Replacements of the same sibling range produce an error'."""


@pytest.mark.xfail(
    reason="Range dominance filtering not yet active: _RewriteActions has no logic to suppress a dominated sibling-range replacement",
    strict=True,
)
@scenario(_FEATURE, "Sibling range dominates a proper subrange regardless of collection order")
def test_sibling_range_dominates_proper_subrange():
    """AI: Scenario test for 'Sibling range dominates a proper subrange regardless of collection order'."""


@pytest.mark.xfail(
    reason="Range dominance filtering not yet active: _RewriteActions has no logic to suppress a dominated sibling-range replacement",
    strict=True,
)
@scenario(_FEATURE, "Sibling range dominates a single contained sibling regardless of collection order")
def test_sibling_range_dominates_single_sibling():
    """AI: Scenario test for 'Sibling range dominates a single contained sibling regardless of collection order'."""


@scenario(_FEATURE, "Prepends of same node are applied in order of collection.")
def test_prepends_of_same_node_in_order():
    """AI: Scenario test for 'Prepends of same node are applied in order of collection.'."""


@pytest.mark.xfail(
    reason="Appends of the same node are applied in collection order, not reversed order as documented",
    strict=True,
)
@scenario(_FEATURE, "Appends of same node are applied in reversed order of collection.")
def test_appends_of_same_node_in_reversed_order():
    """AI: Scenario test for 'Appends of same node are applied in reversed order of collection.'."""


@pytest.mark.xfail(
    reason="Surround-after texts of the same node are applied in collection order, not reversed order as documented",
    strict=True,
)
@scenario(_FEATURE, "Surrounds of same node: before texts in collection order, after texts in reversed collection order")
def test_surrounds_of_same_node():
    """AI: Scenario test for 'Surrounds of same node' before/after text ordering."""


@scenario(_FEATURE, "Surround of ancestor precedes surround of descendant at shared start location regardless of collection order")
def test_surround_ancestor_precedes_surround_descendant_start():
    """AI: Scenario test for 'Surround of ancestor precedes surround of descendant at shared start location'."""


@scenario(_FEATURE, "Surround of descendant precedes surround of ancestor at shared end location regardless of collection order")
def test_surround_descendant_precedes_surround_ancestor_end():
    """AI: Scenario test for 'Surround of descendant precedes surround of ancestor at shared end location'."""


@scenario(_FEATURE, "Prepend is outside surround of the same node \u2014 prepend collected first")
def test_prepend_outside_surround_prepend_first():
    """AI: Scenario test for 'Prepend is outside surround of the same node' (prepend collected first)."""


@pytest.mark.xfail(
    reason="Insertion ordering not yet AST-aware: Rewriter orders by collection order, not AST structure, "
    "so surround collected after prepend incorrectly ends up outside it",
    strict=True,
)
@scenario(_FEATURE, "Prepend is outside surround of the same node \u2014 surround collected first")
def test_prepend_outside_surround_surround_first():
    """AI: Scenario test for 'Prepend is outside surround of the same node' (surround collected first)."""


@pytest.mark.xfail(
    reason="Insertion ordering not yet AST-aware: Rewriter orders by collection order, not AST structure, "
    "so append collected before surround incorrectly ends up outside it",
    strict=True,
)
@scenario(_FEATURE, "Append is outside surround of the same node \u2014 append collected first")
def test_append_outside_surround_append_first():
    """AI: Scenario test for 'Append is outside surround of the same node' (append collected first)."""


@scenario(_FEATURE, "Append is outside surround of the same node \u2014 surround collected first")
def test_append_outside_surround_surround_first():
    """AI: Scenario test for 'Append is outside surround of the same node' (surround collected first)."""


@scenario(_FEATURE, "Prepend appears before replacement of the same node \u2014 prepend collected first")
def test_prepend_before_replacement_prepend_first():
    """AI: Scenario test for 'Prepend appears before replacement of the same node' (prepend collected first)."""


@pytest.mark.xfail(
    reason="Insertion ordering not yet AST-aware: Rewriter orders by collection order, not AST structure, "
    "so a replace collected before prepend incorrectly ends up before it",
    strict=True,
)
@scenario(_FEATURE, "Prepend appears before replacement of the same node \u2014 replace collected first")
def test_prepend_before_replacement_replace_first():
    """AI: Scenario test for 'Prepend appears before replacement of the same node' (replace collected first)."""


@scenario(_FEATURE, "Replacement appears before append of the same node \u2014 replace collected first")
def test_replacement_before_append_replace_first():
    """AI: Scenario test for 'Replacement appears before append of the same node' (replace collected first)."""


@scenario(_FEATURE, "Replacement appears before append of the same node \u2014 append collected first")
def test_replacement_before_append_append_first():
    """AI: Scenario test for 'Replacement appears before append of the same node' (append collected first)."""


@pytest.mark.xfail(
    reason="Insertion ordering not yet AST-aware: Rewriter orders by collection order, not AST structure, "
    "so a replace collected before surround incorrectly ends up before it",
    strict=True,
)
@scenario(_FEATURE, "Surround wraps replacement of the same node \u2014 replace collected first")
def test_surround_wraps_replacement_replace_first():
    """AI: Scenario test for 'Surround wraps replacement of the same node' (replace collected first)."""


@scenario(_FEATURE, "Surround wraps replacement of the same node \u2014 surround collected first")
def test_surround_wraps_replacement_surround_first():
    """AI: Scenario test for 'Surround wraps replacement of the same node' (surround collected first)."""


@pytest.mark.xfail(
    reason="Insertion ordering not yet AST-aware: Rewriter orders by collection order, not AST structure, "
    "so a descendant prepend collected before the ancestor's surround incorrectly ends up outside it",
    strict=True,
)
@scenario(_FEATURE, "Prepend of descendant is inside surround of ancestor at shared start location \u2014 prepend collected first")
def test_prepend_descendant_inside_surround_ancestor_start_prepend_first():
    """AI: Scenario test for 'Prepend of descendant is inside surround of ancestor at shared start location' (prepend collected first)."""


@scenario(_FEATURE, "Prepend of descendant is inside surround of ancestor at shared start location \u2014 surround collected first")
def test_prepend_descendant_inside_surround_ancestor_start_surround_first():
    """AI: Scenario test for 'Prepend of descendant is inside surround of ancestor at shared start location' (surround collected first)."""


@scenario(_FEATURE, "Append of descendant is inside surround of ancestor at shared end location \u2014 append collected first")
def test_append_descendant_inside_surround_ancestor_end_append_first():
    """AI: Scenario test for 'Append of descendant is inside surround of ancestor at shared end location' (append collected first)."""


@pytest.mark.xfail(
    reason="Insertion ordering not yet AST-aware: Rewriter orders by collection order, not AST structure, "
    "so the ancestor's surround collected after the descendant's append incorrectly ends up inside it",
    strict=True,
)
@scenario(_FEATURE, "Append of descendant is inside surround of ancestor at shared end location \u2014 surround collected first")
def test_append_descendant_inside_surround_ancestor_end_surround_first():
    """AI: Scenario test for 'Append of descendant is inside surround of ancestor at shared end location' (surround collected first)."""


@scenario(_FEATURE, "Surround of descendant is inside prepend of ancestor at shared start location \u2014 prepend collected first")
def test_surround_descendant_inside_prepend_ancestor_start_prepend_first():
    """AI: Scenario test for 'Surround of descendant is inside prepend of ancestor at shared start location' (prepend collected first)."""


@pytest.mark.xfail(
    reason="Insertion ordering not yet AST-aware: Rewriter orders by collection order, not AST structure, "
    "so the descendant's surround collected after the ancestor's prepend incorrectly ends up outside it",
    strict=True,
)
@scenario(_FEATURE, "Surround of descendant is inside prepend of ancestor at shared start location \u2014 surround collected first")
def test_surround_descendant_inside_prepend_ancestor_start_surround_first():
    """AI: Scenario test for 'Surround of descendant is inside prepend of ancestor at shared start location' (surround collected first)."""


@pytest.mark.xfail(
    reason="Insertion ordering not yet AST-aware: Rewriter orders by collection order, not AST structure, "
    "so the ancestor's append collected before the descendant's surround incorrectly ends up inside it",
    strict=True,
)
@scenario(_FEATURE, "Surround of descendant is inside append of ancestor at shared end location \u2014 append collected first")
def test_surround_descendant_inside_append_ancestor_end_append_first():
    """AI: Scenario test for 'Surround of descendant is inside append of ancestor at shared end location' (append collected first)."""


@scenario(_FEATURE, "Surround of descendant is inside append of ancestor at shared end location \u2014 surround collected first")
def test_surround_descendant_inside_append_ancestor_end_surround_first():
    """AI: Scenario test for 'Surround of descendant is inside append of ancestor at shared end location' (surround collected first)."""


# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture
def context() -> dict:
    """AI: Return a fresh dict used as shared step-to-step state for a scenario."""
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


def _find_cpp_statement(atu, cpp_factory: CPPPatternFactory, text: str):
    """Return the first C++ statement in the ATU's compound body matching *text*."""
    pattern = list(cpp_factory.create_statements(text))
    assert pattern, f"No C++ pattern created for {text!r}"
    bodies = find_nodes(atu, is_clang_compound_statement)
    for body in bodies:
        matches = match_pattern(body.children, pattern)
        if matches:
            return matches[0].nodes[0]
    raise AssertionError(f"No C++ statement matching {text!r} found")


# ── Given steps ───────────────────────────────────────────────────────────────


@given("a Python language factory")
def given_python_factory(context: dict) -> None:
    """AI: Register a Python RST-based language factory in the context."""
    context["factory"] = PythonFactory(PythonRstNode)


@given("a C++ language factory")
def given_cpp_factory(context: dict) -> None:
    """AI: Register a C++ pattern factory in the context."""
    context["cpp_factory"] = CPPPatternFactory(ASTFactory(ClangASTNode))


@given(parsers.parse("the source '{source}'"))
def given_source(context: dict, source: str) -> None:
    """AI: Parse the given source into an ATU and rewriter, using whichever language factory is registered."""
    source = source.replace("\\n", "\n")
    context["source"] = source
    if "cpp_factory" in context:
        cpp_factory: CPPPatternFactory = context["cpp_factory"]
        stmts = list(cpp_factory.create_statements(source))
        assert stmts, f"No statements parsed from C++ source: {source!r}"
        context["atu"] = stmts[0].root
        context["rewriter"] = ASTRewriter(context["atu"])
    else:
        factory: PythonFactory = context["factory"]
        context["atu"] = factory.create_from_text(source, "test.py")
        context["rewriter"] = ASTRewriter(context["atu"])


# ── Node-selection Given steps ────────────────────────────────────────────────


@given(parsers.parse("the statement '{text}' is a node"))
def given_statement_as_node(context: dict, text: str) -> None:
    """AI: Locate the matching statement and store it as the target node."""
    context["node"] = _find_statement(context["atu"], context["factory"], text)


@given(parsers.parse("the statement '{text}' is the parent node"))
def given_statement_as_parent(context: dict, text: str) -> None:
    """AI: Locate the matching statement and store it as the parent node."""
    context["parent"] = _find_statement(context["atu"], context["factory"], text)


@given("the first leaf of the parent is the child node")
def given_first_leaf_of_parent_as_child(context: dict) -> None:
    """AI: Store the parent's leftmost leaf as the child node."""
    context["child"] = _first_leaf(context["parent"])


@given(parsers.parse("the statement '{text}' is the ancestor node"))
def given_statement_as_ancestor(context: dict, text: str) -> None:
    """AI: Locate the matching statement and store it as the ancestor node."""
    context["ancestor"] = _find_statement(context["atu"], context["factory"], text)


@given("the first leaf of the ancestor is the descendant node")
def given_first_leaf_as_descendant(context: dict) -> None:
    """AI: Store the ancestor's leftmost leaf as the descendant node."""
    context["descendant"] = _first_leaf(context["ancestor"])


@given("the last leaf of the ancestor is the descendant node")
def given_last_leaf_as_descendant(context: dict) -> None:
    """AI: Store the ancestor's rightmost leaf as the descendant node."""
    context["descendant"] = _last_leaf(context["ancestor"])


@given(parsers.parse("the statement '{text}' is the first sibling"))
def given_first_sibling(context: dict, text: str) -> None:
    """AI: Locate the matching statement and store it as the first sibling."""
    if "cpp_factory" in context:
        context["sibling1"] = _find_cpp_statement(context["atu"], context["cpp_factory"], text)
    else:
        context["sibling1"] = _find_statement(context["atu"], context["factory"], text)


@given(parsers.parse("the statement '{text}' is the second sibling"))
def given_second_sibling(context: dict, text: str) -> None:
    """AI: Locate the matching statement and store it as the second sibling."""
    if "cpp_factory" in context:
        context["sibling2"] = _find_cpp_statement(context["atu"], context["cpp_factory"], text)
    else:
        context["sibling2"] = _find_statement(context["atu"], context["factory"], text)


@given(parsers.parse("the statement '{text}' is the third sibling"))
def given_third_sibling(context: dict, text: str) -> None:
    """AI: Locate the matching statement and store it as the third sibling."""
    context["sibling3"] = _find_statement(context["atu"], context["factory"], text)


# ── When steps ────────────────────────────────────────────────────────────────


@when(parsers.parse("the node is replaced with '{text}'"))
def when_replace_node(context: dict, text: str) -> None:
    """AI: Replace the target node with the given text."""
    context["rewriter"].replace(text, [context["node"]])


@when(parsers.parse("the parent node is replaced with '{text}'"))
def when_replace_parent(context: dict, text: str) -> None:
    """AI: Replace the parent node with the given text."""
    context["rewriter"].replace(text, [context["parent"]])


@when(parsers.parse("the child node is prepended with '{text}'"))
def when_prepend_child(context: dict, text: str) -> None:
    """AI: Insert the given text before the child node."""
    context["rewriter"].insert_before(text, [context["child"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the first and second siblings are replaced with '{text}'"))
def when_replace_first_second(context: dict, text: str) -> None:
    """AI: Replace the first and second siblings together with the given text."""
    context["rewriter"].replace(text, [context["sibling1"], context["sibling2"]])


@when(parsers.parse("the second and third siblings are replaced with '{text}'"))
def when_replace_second_third(context: dict, text: str) -> None:
    """AI: Replace the second and third siblings together with the given text."""
    context["rewriter"].replace(text, [context["sibling2"], context["sibling3"]])


@when(parsers.parse("the first, second and third siblings are replaced with '{text}'"))
def when_replace_first_second_third(context: dict, text: str) -> None:
    """AI: Replace the first, second, and third siblings together with the given text."""
    context["rewriter"].replace(text, [context["sibling1"], context["sibling2"], context["sibling3"]])


@when(parsers.parse("the second sibling is replaced with '{text}'"))
def when_replace_second_sibling(context: dict, text: str) -> None:
    """AI: Replace the second sibling with the given text."""
    context["rewriter"].replace(text, [context["sibling2"]])


@when(parsers.parse("the node is prepended with '{text}'"))
def when_prepend_node(context: dict, text: str) -> None:
    """AI: Insert the given text before the target node."""
    context["rewriter"].insert_before(text, [context["node"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the node is appended with '{text}'"))
def when_append_node(context: dict, text: str) -> None:
    """AI: Insert the given text after the target node."""
    context["rewriter"].insert_after(text, [context["node"]], include_whitespace=False, include_comments=False)


@when(parsers.re(r"the node is surrounded with '(?P<before>[^']*)' and '(?P<after>[^']*)'"))
def when_surround_node(context: dict, before: str, after: str) -> None:
    """AI: Insert text before and after the target node."""
    context["rewriter"].insert_before(before, [context["node"]], include_whitespace=False, include_comments=False)
    context["rewriter"].insert_after(after, [context["node"]], include_whitespace=False, include_comments=False)


@when(parsers.re(r"the (?P<role>ancestor|descendant) is surrounded with '(?P<before>[^']*)' and '(?P<after>[^']*)'"))
def when_surround_by_role(context: dict, role: str, before: str, after: str) -> None:
    """AI: Insert text before and after the node identified by role (ancestor or descendant)."""
    context["rewriter"].insert_before(before, [context[role]], include_whitespace=False, include_comments=False)
    context["rewriter"].insert_after(after, [context[role]], include_whitespace=False, include_comments=False)


# Role-dispatching steps used by the Scenario Outlines for scenarios 4 and 5.
# The role ("ancestor" or "descendant") is looked up directly in the context
# fixture, making it possible to parameterize the collection order in the
# Examples table without duplicating step definitions.
@when(parsers.re(r"the (?P<role>ancestor|descendant) is prepended with '(?P<text>[^']*)'"))
def when_prepend_by_role(context: dict, role: str, text: str) -> None:
    """AI: Insert text before the node identified by role (ancestor or descendant)."""
    context["rewriter"].insert_before(text, [context[role]], include_whitespace=False, include_comments=False)


@when(parsers.re(r"the (?P<role>ancestor|descendant) is appended with '(?P<text>[^']*)'"))
def when_append_by_role(context: dict, role: str, text: str) -> None:
    """AI: Insert text after the node identified by role (ancestor or descendant)."""
    context["rewriter"].insert_after(text, [context[role]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the first sibling is appended with '{text}'"))
def when_append_first_sibling(context: dict, text: str) -> None:
    """AI: Insert the given text after the first sibling."""
    context["rewriter"].insert_after(text, [context["sibling1"]], include_whitespace=False, include_comments=False)


@when(parsers.parse("the second sibling is prepended with '{text}'"))
def when_prepend_second_sibling(context: dict, text: str) -> None:
    """AI: Insert the given text before the second sibling."""
    context["rewriter"].insert_before(text, [context["sibling2"]], include_whitespace=False, include_comments=False)


@when(parsers.re(r"the first sibling is surrounded with '(?P<before>[^']*)' and '(?P<after>[^']*)'"))
def when_surround_first_sibling(context: dict, before: str, after: str) -> None:
    """AI: Insert text before and after the first sibling."""
    context["rewriter"].insert_before(before, [context["sibling1"]], include_whitespace=False, include_comments=False)
    context["rewriter"].insert_after(after, [context["sibling1"]], include_whitespace=False, include_comments=False)


@when(parsers.re(r"the second sibling is surrounded with '(?P<before>[^']*)' and '(?P<after>[^']*)'"))
def when_surround_second_sibling(context: dict, before: str, after: str) -> None:
    """AI: Insert text before and after the second sibling."""
    context["rewriter"].insert_before(before, [context["sibling2"]], include_whitespace=False, include_comments=False)
    context["rewriter"].insert_after(after, [context["sibling2"]], include_whitespace=False, include_comments=False)


# ── Then steps ────────────────────────────────────────────────────────────────


@then("applying the changes raises an error")
def then_applying_raises_error(context: dict) -> None:
    """AI: Assert that applying the collected rewrites raises an error."""
    with pytest.raises(ValueError, match="Conflicting rewrites"):
        context["rewriter"].apply_to_string()


@then(parsers.parse("the result contains '{text}'"))
def then_result_contains(context: dict, text: str) -> None:
    """AI: Assert that the given text appears in the rewritten result."""
    result = context["rewriter"].apply_to_string()
    assert text in result, f"Expected {text!r} in result, got: {result!r}"


@then(parsers.parse("the result does not contain '{text}'"))
def then_result_not_contains(context: dict, text: str) -> None:
    """AI: Assert that the given text does not appear in the rewritten result."""
    result = context["rewriter"].apply_to_string()
    assert text not in result, f"Did not expect {text!r} in result, got: {result!r}"


@then(parsers.parse("'{a}' appears before '{b}' in the result"))
def then_a_before_b(context: dict, a: str, b: str) -> None:
    """AI: Assert that text *a* appears before text *b* in the rewritten result."""
    result = context["rewriter"].apply_to_string()
    pos_a = result.find(a)
    pos_b = result.find(b)
    assert pos_a != -1, f"Expected {a!r} in result, got: {result!r}"
    assert pos_b != -1, f"Expected {b!r} in result, got: {result!r}"
    assert pos_a < pos_b, f"Expected {a!r} (at {pos_a}) to appear before {b!r} (at {pos_b}) in result: {result!r}"

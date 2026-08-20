"""
Property-based tests for rewrite semantics.

Audience: developers and testers.

These tests use Hypothesis to verify that the rewrite-semantics rules hold
universally, complementing the representative BDD examples in:
  features/rewrite-semantics.feature

Each test references the BDD scenario it universally covers and the concept
rule it enforces (CONCEPT-REWRITE-SEMANTICS).
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.syntax_tree import ASTRewriter
from renaissance.syntax_tree.match_finder import match_pattern

# ── Strategies ────────────────────────────────────────────────────────────────

_SIMPLE_ASSIGNMENTS = st.sampled_from([
    "a = 1",
    "b = 2",
    "x = 'hello'",
    "result = True",
    "n = 0",
])

_REPLACEMENT_TEXTS = st.one_of(
    st.sampled_from(["A", "B", "a = 99", "z = z", "pass", ""]),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=8),
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_and_find(source: str):
    factory = PythonFactory(PythonRstNode)
    atu = factory.create_from_text(source + "\n", "test.py")
    pattern_factory = PythonPatternFactory(factory)
    pattern = pattern_factory.create_statements(source)
    matches = match_pattern(atu.children, pattern)
    return factory, atu, matches


# ── Property tests ────────────────────────────────────────────────────────────

@pytest.mark.xfail(
    reason="Replacing the same node twice is not yet rejected: ASTRewriter does not validate for duplicate replacements",
    strict=True,
)
@settings(max_examples=50)
@given(source=_SIMPLE_ASSIGNMENTS, first=_REPLACEMENT_TEXTS, second=_REPLACEMENT_TEXTS)
def test_replacing_same_node_twice_always_errors(
    source: str, first: str, second: str
) -> None:
    """Property: replacing the same AST node twice always raises, regardless of
    the replacement texts and regardless of whether they are equal.

    BDD counterpart : Scenario 0 in features/rewrite-semantics.feature
                      ("Replacements of the same node produce an error")
    Rule source     : CONCEPT-REWRITE-SEMANTICS
                      docs/user/concepts/rewrite-semantics.md
    """
    _, atu, matches = _parse_and_find(source)
    assume(len(matches) > 0)
    node = matches[0].nodes[0]

    rewriter = ASTRewriter(atu)
    rewriter.replace(first, [node])
    rewriter.replace(second, [node])

    with pytest.raises(Exception):
        rewriter.apply_to_string()

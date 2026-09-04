from pathlib import Path

import pytest

from features.steps.test_steps import *

FEATURES_BASE_DIR = Path(__file__).resolve().parent.parent

# Tags on individual `Examples:` blocks in features/rewrite-semantics.feature that
# mark one specific collection-order case as a known, not-yet-fixed failure. The
# Rewriter currently orders prepend/append text by collection order rather than
# AST structure, so only ONE of the two collection orders in each scenario
# actually fails — the other passes by coincidence and must stay a real test,
# so the xfail can't be applied to the whole Scenario Outline.
#
# pytest-bdd applies Examples-block tags as bare `pytest.mark.<tag>` marks (with
# no arguments, and bypassing the `pytest_bdd_apply_tag` hook — see
# `collect_example_parametrizations` in pytest_bdd/scenario.py), so a
# `pytest_collection_modifyitems` hook converts each tag into a properly
# configured `xfail(reason=..., strict=True)` marker after collection.
_XFAIL_TAGS = {
    "xfail_prepend_descendant_first": {
        "reason": "Prepend ordering not yet enforced when descendant is collected "
        "first: Rewriter orders prepends by collection order, not AST structure",
        "strict": True,
    },
    "xfail_append_ancestor_first": {
        "reason": "Append ordering (descendant before ancestor) not yet enforced "
        "when ancestor is collected first: Rewriter appends in insertion order",
        "strict": True,
    },
    "xfail_sibling_range_dominance_range_first": {
        "reason": "Range dominance not yet enforced when the dominating range is "
        "collected first: _RewriteActions has no range-dominance filtering",
        "strict": True,
    },
    "xfail_surround_descendant_first_shared_start": {
        "reason": "Surround-before ordering not yet enforced when descendant is "
        "collected first: Rewriter orders surround-before texts by collection order, not AST structure",
        "strict": True,
    },
    "xfail_surround_ancestor_first_shared_end": {
        "reason": "Surround-after ordering not yet enforced when ancestor is "
        "collected first: Rewriter orders surround-after texts by collection order, not AST structure",
        "strict": True,
    },
}


def pytest_collection_modifyitems(items):
    for item in items:
        for tag, xfail_kwargs in _XFAIL_TAGS.items():
            if item.get_closest_marker(tag) is not None:
                item.add_marker(pytest.mark.xfail(**xfail_kwargs))

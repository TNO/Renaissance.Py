<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.match.match_finder

{ #codemod-core-match-match-finder }

**Stable ID:** `CODEMOD-CORE-MATCH-MATCH-FINDER`

## Responsibility

The matcher: finding the occurrences of a pattern in a tree, with their placeholder bindings.

## Location

`src/renaissance/core/match/match_finder.py`

## Public entry points

`renaissance.core.match` exports:

- `match_pattern(src_nodes, patterns, recursive)`: the matches of a sequence of pattern nodes in a sequence of nodes, also in
  their descendants when `recursive` is true.
- `find_all(src_nodes, *patterns, recursive)`: the matches of any of several patterns.
- `MatchFinder`: `match_pattern` and `find_all` as static methods.
- `PatternMatch`: a match: the matched nodes, the patterns, and the nodes bound to each placeholder.
- `is_match(src, cmp)`: whether one node matches one pattern node.
- `find_in_list(src, cmp, exp, start)`: the end index of the first match of a sequence of pattern nodes from `start`.

## Internal structure

`find_variants` finds every way in which a sequence of pattern nodes matches, as a `Variant` each; a placeholder for a
sequence of nodes can make several variants, and the most greedy one comes first.

## Validated by test modules

- `test/unit/core/match/test_match_finder___match_dict.py`
- `test/unit/core/match/test_match_finder___match_tree.py`
- `test/unit/core/match/test_match_finder___multi_assignments.py`
- `test/unit/core/match/test_match_finder___one_and_all_params.py`
- `test/unit/core/match/test_match_finder___pattern_match.py`

And the matcher tests of the parser bindings in `test/c_cpp/`, `test/lst/` and `test/python/ast/`.

## Related concepts

- [Match](../../../user/core/match/match.md)
- [Pattern](../../../user/core/pattern/pattern.md)
- [Matching](../../../user/concepts/matching.md)

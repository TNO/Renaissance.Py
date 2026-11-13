<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core match

{ #codemod-core-match }

**Stable ID:** `CODEMOD-CORE-MATCH`

## Responsibility

The matcher: finding the occurrences of a pattern in a tree, with their placeholder bindings.

## Location

`src/renaissance/core/match/`

## Public entry points

The `__all__` of `renaissance.core.match`; see the [API reference](../../api/core/match.md).

- `match_pattern(src_nodes, patterns, recursive)`: the matches of a sequence of pattern nodes in a sequence of nodes, also in
  their descendants when `recursive` is true.
- `find_all(src_nodes, *patterns, recursive)`: the matches of any of several patterns.
- `MatchFinder`: `match_pattern` and `find_all` as static methods.
- `PatternMatch`: a match: the matched nodes, the patterns, and the nodes bound to each placeholder.
- `is_match(src, cmp)`: whether one node matches one pattern node.
- `find_in_list(src, cmp, exp, start)`: the end index of the first match of a sequence of pattern nodes from `start`.

## Internal structure

`match_finder.py` defines the matcher. `find_variants` finds every way in which a sequence of pattern nodes matches, as a
`Variant` each; a placeholder for a sequence of nodes can make several variants, and the most greedy one comes first.

`core.match` imports `core.model` and `core.pattern`.

## Related features

- [Pattern matching](../../../user/features/pattern_matching.md)

## Related concepts

- [Match](../../../user/core/match.md)
- [Pattern](../../../user/core/pattern.md)
- [Matching](../../../user/concepts/matching.md)

## Validated by test modules

`test/unit/core/match/`, and the matcher tests of the parser bindings in `test/c_cpp/`, `test/lst/` and `test/python/ast/`.

## Extension points

A parser binding presents its nodes through `NodeProtocol`; the matcher compares their kinds, properties and children.

## Non-goals

Changing the code, which is the task of the rewriter.

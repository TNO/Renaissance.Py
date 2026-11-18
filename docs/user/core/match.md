<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Match

{ #concept-core-match }

**Stable ID:** `CONCEPT-CORE-MATCH`

## Purpose

Describe how a pattern is found in code.

## Scope

Finding the occurrences of a pattern in a tree, whatever the language of the source code.

## Definition

- `match_pattern(nodes, pattern)` returns the matches of a pattern, a sequence of pattern nodes, in a sequence of nodes, and in
  their descendants. `find_all(nodes, *patterns)` does the same for several patterns.
- A match, a `PatternMatch`, holds the matched nodes and, for each placeholder of the pattern, the nodes bound to it.
  `match["$x"]` gives the text of the nodes bound to `$x`.
- `is_match(node, pattern)` tells whether one node matches one pattern node.

## Invariants / guarantees

- A placeholder for one node, such as `$x`, that occurs more than once in a pattern matches equal nodes at each occurrence.

## Related features

- [Pattern matching](../features/pattern_matching.md)

## Related tests

`test/unit/core/match/`

## Related code

`src/renaissance/core/match/`

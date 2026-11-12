<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Pattern

{ #concept-core-pattern }

**Stable ID:** `CONCEPT-CORE-PATTERN`

## Purpose

Describe how a pattern names its variable parts: its placeholders.

## Scope

The notation of placeholders in a pattern, whatever the language of the source code.

## Definition

- `$name` is a placeholder for one node; `$$name` is a placeholder for a sequence of nodes. `PatternKind` names these two
  kinds: `MATCH_ONE` and `MATCH_ALL`.
- Not every parser accepts `$` in a name, so `replace_dollar(text)` replaces `$$` by `MATCH_ALL` and `$` by `MATCH_ONE`
  before such a parser parses the pattern. `use_dollar(text)` does the reverse.
- `detect_placeholder(signature, node_type)` tells whether the signature of a node is a placeholder, and of which kind.

## Invariants / guarantees

- The notation is the same for every language.

## Related features

- [Pattern matching](../features/pattern_matching.md)

## Related tests

`test/unit/core/pattern/`

## Related code

`src/renaissance/core/pattern/`

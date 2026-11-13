<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core pattern

{ #codemod-core-pattern }

**Stable ID:** `CODEMOD-CORE-PATTERN`

## Responsibility

The pattern language: the placeholders in a pattern and the kinds of pattern matching.

## Location

`src/renaissance/core/pattern/`

## Public entry points

The `__all__` of `renaissance.core.pattern`; see the [API reference](../../api/core/pattern.md).

- `PatternKind`: the kinds of placeholder, `MATCH_ONE` and `MATCH_ALL`.
- `MATCH_ONE` and `MATCH_ALL`: the markers that replace `$` and `$$` in a pattern for a parser that does not accept `$`.
- `replace_dollar` and `use_dollar`: the conversion between the dollar notation and the markers.
- `detect_placeholder`: whether the signature of a node is a placeholder, and of which kind.

## Internal structure

- `pattern_kind.py` defines `PatternKind`.
- `placeholders.py` defines the markers and the functions.

`core.pattern` imports nothing from the rest of the core.

## Related features

- [Pattern matching](../../../user/features/pattern_matching.md)

## Related concepts

- [Pattern](../../../user/core/pattern.md)
- [Matching](../../../user/concepts/matching.md)

## Validated by test modules

`test/unit/core/pattern/`

## Extension points

A parser binding whose parser does not accept `$` in a name calls `replace_dollar` before it parses a pattern. A binding may
use `detect_placeholder` to recognize its placeholders.

## Non-goals

Matching a pattern against code, which is the task of the matcher.

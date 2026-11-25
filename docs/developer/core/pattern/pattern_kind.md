<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.pattern.pattern_kind

{ #codemod-core-pattern-pattern-kind }

**Stable ID:** `CODEMOD-CORE-PATTERN-PATTERN-KIND`

## Responsibility

The kinds of placeholder: one node versus a sequence of nodes.

## Location

`src/renaissance/core/pattern/pattern_kind.py`

## Public entry points

`renaissance.core.pattern` exports `PatternKind`, with the kinds `MATCH_ONE` and `MATCH_ALL`.

## Internal structure

`PatternKind` is an enumeration; it depends on no other module.

## Validated by test modules

- `test/unit/core/pattern/test_pattern_kind.py`

## Related concepts

- [Pattern](../../../user/core/pattern/pattern.md)

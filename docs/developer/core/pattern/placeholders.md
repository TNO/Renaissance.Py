<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.pattern.placeholders

{ #codemod-core-pattern-placeholders }

**Stable ID:** `CODEMOD-CORE-PATTERN-PLACEHOLDERS`

## Responsibility

The notation of placeholders: the conversion of the dollar notation, and the detection of a placeholder.

## Location

`src/renaissance/core/pattern/placeholders.py`

## Public entry points

`renaissance.core.pattern` exports:

- `MATCH_ONE` and `MATCH_ALL`: the markers that replace `$` and `$$` in a pattern for a parser that does not accept `$`;
- `replace_dollar` and `use_dollar`: the conversion between the dollar notation and the markers;
- `detect_placeholder`: whether the signature of a node is a placeholder, and of which kind.

## Internal structure

The markers and functions work on strings; they depend on no other module.

## Validated by test modules

None yet.

## Related concepts

- [Pattern](../../../user/core/pattern/pattern.md)

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.shared.equal

{ #codemod-parser-bindings-shared-equal }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-SHARED-EQUAL`

## Responsibility

Compares the properties and the children of two nodes, with which a parser binding implements `__eq__`.

## Location

`src/renaissance/parser_bindings/shared/equal.py`

## Public entry points

`renaissance.parser_bindings.shared` exports `equal_in_properties(mine, other, is_relevant_property)` and
`equal_in_children(mine, other, is_relevant_child)`.

## Internal structure

Both functions filter each side with the predicate of the binding and compare the results, so the comparison is symmetric.

The module imports only the standard library.

## Validated by test modules

- `test/unit/parser_bindings/shared/test_equal.py`

## Related concepts

- [Shared helpers of the parser bindings](../../../user/parser_bindings/shared/shared.md)

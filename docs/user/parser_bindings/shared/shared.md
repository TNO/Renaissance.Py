<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Shared helpers of the parser bindings

{ #concept-parser-bindings-shared }

**Stable ID:** `CONCEPT-PARSER-BINDINGS-SHARED`

## Purpose

Describe the helpers with which a parser binding, in tree or out of tree, implements the model.

## Scope

The helpers that several parser bindings use. It is not a binding itself.

## Definition

- `equal_in_properties(mine, other, is_relevant_property)` returns whether two mappings of properties have the same relevant
  properties with equal values.
- `equal_in_children(mine, other, is_relevant_child)` returns whether two sequences of children have the same relevant children
  in the same order.

A binding implements node equality with them, and passes its own facts, such as the properties that equality ignores.

## Invariants / guarantees

- The helpers import nothing from Renaissance.Py.
- A helper takes the facts of a binding as parameters, so no binding shares its data with another.

## Extension points

None.

## Non-goals

Sharing data, such as kind maps, between bindings.

## Related features

None.

## Related tests

`test/unit/parser_bindings/shared/`

## Related code

`src/renaissance/parser_bindings/shared/`

## API

::: renaissance.parser_bindings.shared
    options:
      heading_level: 3

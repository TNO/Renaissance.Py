<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core model

{ #concept-core-model }

**Stable ID:** `CONCEPT-CORE-MODEL`

## Purpose

Describe what every node of a syntax tree offers, whatever the language of the source code.

## Scope

The information that finding, matching and rewriting rely on. Which nodes a tree contains depends on the language.

## Definition

Every node has:

- `parser_kind`: the kind of the node, as the parser names it;
- `semantic_kind`: a language-independent kind, such as `FUNCTION`, `CALL` or `LITERAL`, or `NODE` if no such kind applies;
- `properties`: further attributes of the node;
- `children`: its child nodes, in source order;
- `signature`: its source text;
- `name`: its declared name, or an empty string if it has none.

## Invariants / guarantees

- The semantic kinds are the same for every language.
- `semantic_kind` is a coarse classification; use `parser_kind` when the exact construct matters.

## Related features

- [Parsing and AST access](../features/parsing-and-ast-access.md)

## Related tests

`test/unit/core/model/`

## Related code

`src/renaissance/core/model/`

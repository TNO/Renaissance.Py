<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Rewrite

{ #concept-core-rewrite }

**Stable ID:** `CONCEPT-CORE-REWRITE`

## Purpose

Describe how code is changed.

## Scope

Replacing parts of the content of a file, whatever the language of the source code.

## Definition

- An `ASTRewriter` holds the code of a node, and collects changes of nodes or pattern matches in it: `replace`, `remove`,
  `insert_before` and `insert_after`. `apply()` returns the changed code as bytes, and `apply_to_string()` as a string.
- A `Rewriter` holds the content of a file, as bytes, and collects replacements of byte ranges of it.
- `replace(start, end, new_content)` adds a replacement; `apply()` returns the content with all replacements applied, and
  leaves the content of the rewriter unchanged.

## Invariants / guarantees

- The positions of the replacements refer to the original content, whatever the order in which they are added.
- `ASTRewriter.apply()` raises a `ValueError` when two replacements or removals overlap, unless one node contains the
  other.

## Related features

- [Rewrite semantics](../features/rewrite_semantics.md)

## Related tests

`test/unit/core/rewrite/`

## Related code

`src/renaissance/core/rewrite/`

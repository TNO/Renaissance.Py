<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Refactor actions

{ #concept-recipes-refactor-actions }

**Stable ID:** `CONCEPT-RECIPES-REFACTOR-ACTIONS`

## Purpose

Describe the reusable actions that recipes use to replace code.

## Scope

Replacing code in the tree of one processor.

## Definition

- `ASTRefactorActions` wraps an `ASTProcessor` and a pattern factory.
- `replace_name`, `replace_text` and `replace_expr` replace the name in each node with the given name or text, optionally
  only in nodes of a given kind, and not in nodes of a kind to skip.
- `replace_declaration` replaces each match of a declaration pattern.

## Invariants / guarantees

- The actions collect changes in the processor; they do not commit them.

## Related features

- [Transformation workflows](../features/transformation_workflows.md)

## Related tests

`test/unit/recipes/refactor_actions/`

## Related code

`src/renaissance/recipes/refactor_actions/`

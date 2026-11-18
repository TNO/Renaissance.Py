<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Recipe refactor actions

{ #codemod-recipes-refactor-actions }

**Stable ID:** `CODEMOD-RECIPES-REFACTOR-ACTIONS`

## Responsibility

Reusable refactoring actions: replacing names, texts, expressions and declarations in the tree of one processor.

## Location

`src/renaissance/recipes/refactor_actions/`

## Public entry points

The `__all__` of `renaissance.recipes.refactor_actions`; see the [API reference](../../api/recipes/refactor_actions.md).

- `ASTRefactorActions(processor, pattern_factory)`: collects replacements with `processor`; `replace_expr`, `replace_name`
  and `replace_text` replace the nodes found by name or text, of a given kind; `replace_declaration` replaces the matches of a
  declaration pattern that `pattern_factory` creates; `find_declaration` and `collect` return the matches of a pattern.

## Internal structure

- `ast_refactor_actions.py` defines `ASTRefactorActions`.

`recipes.refactor_actions` imports `core.match`, `core.model` and `core.processing`. Its pattern factory is annotated as a
`CPPPatternFactory` of the clang binding, a known violation, because a pattern factory protocol is missing in the core.

## Related features

- [Transformation workflows](../../../user/features/transformation_workflows.md)

## Related concepts

- [Refactor actions](../../../user/recipes/refactor_actions.md)

## Validated by test modules

`test/unit/recipes/refactor_actions/`

## Extension points

None.

## Non-goals

Committing the changes, which is the task of the processor.

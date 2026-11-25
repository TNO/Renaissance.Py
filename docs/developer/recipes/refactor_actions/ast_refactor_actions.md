<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# recipes.refactor_actions.ast_refactor_actions

{ #codemod-recipes-refactor-actions-ast-refactor-actions }

**Stable ID:** `CODEMOD-RECIPES-REFACTOR-ACTIONS-AST-REFACTOR-ACTIONS`

## Responsibility

Reusable refactoring actions: replacing names, texts, expressions and declarations in the tree of one processor.

## Location

`src/renaissance/recipes/refactor_actions/ast_refactor_actions.py`

## Public entry points

`renaissance.recipes.refactor_actions` exports `ASTRefactorActions(processor, pattern_factory)`: collects replacements with
`processor`; `replace_expr`, `replace_name` and `replace_text` replace the nodes found by name or text, of a given kind;
`replace_declaration` replaces the matches of a declaration pattern that `pattern_factory` creates; `find_declaration` and
`collect` return the matches of a pattern.

## Internal structure

The pattern factory is annotated as a `CPPPatternFactory` of the clang binding, a known violation, because a pattern factory
protocol is missing in the core.

## Validated by test modules

- `test/unit/recipes/refactor_actions/test_ast_refactor_actions.py`

## Related concepts

- [Refactor actions](../../../user/recipes/refactor_actions/refactor_actions.md)

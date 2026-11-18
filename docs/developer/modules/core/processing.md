<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core processing

{ #codemod-core-processing }

**Stable ID:** `CODEMOD-CORE-PROCESSING`

## Responsibility

Running recipes: processors, batch processing, recipe steps and repetition until no change.

## Location

`src/renaissance/core/processing/`

## Public entry points

The `__all__` of `renaissance.core.processing`; see the [API reference](../../api/core/processing.md).

- `ASTProcessor(root, ast_factory, in_memory)`: finds nodes and matches in the tree of `root`, and collects changes of it
  with an `ASTRewriter`; `commit()` applies them, in memory or to the file, and returns a processor of the new tree.
- `BatchASTProcessor(in_memory, max_processes)`: runs actions on a processor of each tree that an iterable provides, in
  parallel threads; `once` runs them one time, `repeat` until no change, at most `max_repeat` times.
- `process_atu`: runs the actions on one tree; `BatchASTProcessor` calls it for each tree.
- `Action`, `IterableProvider` and `AST_FACTORY_AND_ATU`: the types of an action, of a provider of trees, and of one tree
  with its factory.
- `RecipeASTProcessor(recipe, iterable_provider, file_filter)`: runs the methods of `recipe` that are decorated with
  `recipe_step`, `after_step` and `final_action` on the trees that `iterable_provider` provides.

## Internal structure

- `ast_processor.py` defines `ASTProcessor`.
- `batch_ast_processor.py` defines `BatchASTProcessor` and `process_atu`, in terms of `ASTProcessor`.
- `recipe_ast_processor.py` defines `RecipeASTProcessor` and its decorators, in terms of `BatchASTProcessor`.

`core.processing` imports `core.match`, `core.model` and `core.rewrite`.

## Related features

- [Transformation workflows](../../../user/features/transformation_workflows.md)

## Related concepts

- [Processing](../../../user/core/processing.md)

## Validated by test modules

`test/unit/core/processing/`

## Extension points

A recipe is a class whose methods are decorated with `recipe_step`, `after_step` and `final_action`.

## Non-goals

Deciding what to change, which is the task of the recipes.

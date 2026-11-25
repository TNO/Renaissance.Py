<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.processing.recipe_ast_processor

{ #codemod-core-processing-recipe-ast-processor }

**Stable ID:** `CODEMOD-CORE-PROCESSING-RECIPE-AST-PROCESSOR`

## Responsibility

Running a recipe: its steps, the actions after a step, and its final actions.

## Location

`src/renaissance/core/processing/recipe_ast_processor.py`

## Public entry points

`renaissance.core.processing` exports:

- `RecipeASTProcessor(recipe, iterable_provider, file_filter)`: runs the decorated methods of `recipe` on the trees that
  `iterable_provider` provides;
- `recipe_step`, `after_step` and `final_action`: the decorators of the methods of a recipe.

## Internal structure

`RecipeASTProcessor` is defined in terms of `BatchASTProcessor` of [`batch_ast_processor`](batch_ast_processor.md).

## Validated by test modules

- `test/unit/core/processing/test_recipe_ast_processor.py`

## Related concepts

- [Processing](../../../user/core/processing/processing.md)

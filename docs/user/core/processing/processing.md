<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Processing

{ #concept-core-processing }

**Stable ID:** `CONCEPT-CORE-PROCESSING`

## Purpose

Describe how recipes are run on code.

## Scope

Running changes on one file or on many files, whatever the language of the source code.

## Definition

- An `ASTProcessor` holds the tree of one file. It finds nodes and pattern matches in it, and collects changes of it:
  `replace`, `remove`, `insert_before` and `insert_after`. `commit()` applies the changes and returns a processor of the
  new tree.
- A `BatchASTProcessor` runs actions on many files: an action takes an `ASTProcessor`, and may return a function that is
  called afterwards. `once` runs the actions one time; `repeat` runs them until no file changes, at most `max_repeat` times.
- A `RecipeASTProcessor` runs a recipe: the methods decorated with `recipe_step` in the order of their steps, those
  decorated with `after_step` after the step they name, and those decorated with `final_action` at the end.

## Invariants / guarantees

- With `in_memory`, the files are not written; otherwise `commit()` writes the changed file and parses it again.

## Extension points

A recipe is a class whose methods are decorated with `recipe_step`, `after_step` and `final_action`.

## Non-goals

Deciding what to change, which is the task of the recipes.

## Related features

- [Transformation workflows](../../features/transformation_workflows.md)

## Related tests

`test/unit/core/processing/`

## Related code

`src/renaissance/core/processing/`

## API

::: renaissance.core.processing
    options:
      heading_level: 3

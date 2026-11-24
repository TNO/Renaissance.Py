<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.processing.batch_ast_processor

{ #codemod-core-processing-batch-ast-processor }

**Stable ID:** `CODEMOD-CORE-PROCESSING-BATCH-AST-PROCESSOR`

## Responsibility

Processing many trees, in parallel.

## Location

`src/renaissance/core/processing/batch_ast_processor.py`

## Public entry points

`renaissance.core.processing` exports:

- `BatchASTProcessor(in_memory, max_processes)`: runs actions on a processor of each tree that an iterable provides, in
  parallel threads; `once` runs them one time, `repeat` until no change, at most `max_repeat` times;
- `process_atu`: runs the actions on one tree; `BatchASTProcessor` calls it for each tree;
- `Action`, `IterableProvider` and `AST_FACTORY_AND_ATU`: the types of an action, of a provider of trees, and of one tree
  with its factory.

## Internal structure

`BatchASTProcessor` and `process_atu` are defined in terms of `ASTProcessor` of [`ast_processor`](ast_processor.md).

## Validated by test modules

- `test/unit/core/processing/test_batch_ast_processor.py`

## Related concepts

- [Processing](../../../user/core/processing/processing.md)

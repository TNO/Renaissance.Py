<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.processing.ast_processor

{ #codemod-core-processing-ast-processor }

**Stable ID:** `CODEMOD-CORE-PROCESSING-AST-PROCESSOR`

## Responsibility

Processing one tree: finding nodes and matches in it, and changing it.

## Location

`src/renaissance/core/processing/ast_processor.py`

## Public entry points

`renaissance.core.processing` exports `ASTProcessor(root, ast_factory, in_memory)`: finds nodes and matches in the tree of
`root`, and collects changes of it with an `ASTRewriter`; `commit()` applies them, in memory or to the file, and returns a
processor of the new tree.

## Internal structure

`ASTProcessor` is defined in terms of the matcher of [`core.match`](../match/match_finder.md) and the `ASTRewriter` of
[`core.rewrite`](../rewrite/ast_rewriter.md).

## Validated by test modules

- `test/unit/core/processing/test_ast_processor___find_match.py`
- `test/unit/core/processing/test_ast_processor___semantic_kind.py`

## Related concepts

- [Processing](../../../user/core/processing/processing.md)

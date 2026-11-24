<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.rewrite.ast_rewriter

{ #codemod-core-rewrite-ast-rewriter }

**Stable ID:** `CODEMOD-CORE-REWRITE-AST-REWRITER`

## Responsibility

Changing the code by nodes: turning the changes of nodes into replacements of byte ranges.

## Location

`src/renaissance/core/rewrite/ast_rewriter.py`

## Public entry points

`renaissance.core.rewrite` exports:

- `ASTRewriter(node)`: collects changes of the code of `node`: `replace`, `remove`, `insert_before` and `insert_after` of
  nodes or pattern matches; `apply()` returns the changed code as bytes, and `apply_to_string()` as a string;
- `Rewritable`: the protocol of the nodes that `ASTRewriter` changes: their offsets, file name and text.

## Internal structure

`ASTRewriter` turns the changes of nodes into replacements of byte ranges, by default extended with the whitespace and
comments around the nodes, and applies them with a `Rewriter` of [`rewriter`](rewriter.md).

## Validated by test modules

- `test/unit/core/rewrite/test_ast_rewriter___comment_location.py`
- `test/unit/core/rewrite/test_ast_rewriter___composition.py`
- `test/unit/core/rewrite/test_ast_rewriter___remove_replace_insert.py`
- `test/unit/core/rewrite/test_ast_rewriter___semantics.py`

## Related concepts

- [Rewrite](../../../user/core/rewrite/rewrite.md)
- [Rewrite semantics](../../../user/concepts/rewrite_semantics.md)

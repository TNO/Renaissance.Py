<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core rewrite

{ #codemod-core-rewrite }

**Stable ID:** `CODEMOD-CORE-REWRITE`

## Responsibility

The rewriter: changing the code, by nodes and by byte ranges of its content.

## Location

`src/renaissance/core/rewrite/`

## Public entry points

The `__all__` of `renaissance.core.rewrite`; see the [API reference](../../api/core/rewrite.md).

- `ASTRewriter(node)`: collects changes of the code of `node`: `replace`, `remove`, `insert_before` and `insert_after` of
  nodes or pattern matches; `apply()` returns the changed code as bytes, and `apply_to_string()` as a string.
- `Rewritable`: the protocol of the nodes that `ASTRewriter` changes: their offsets, file name and text.
- `Rewriter(content)`: collects replacements of byte ranges of `content`; `replace(start, end, new_content)` adds one, and
  `apply()` returns the content with all of them applied.
- `Rewrite`: one pending replacement: a byte range and its new content.

## Internal structure

`ast_rewriter.py` defines `ASTRewriter`, which turns the changes of nodes into replacements of byte ranges, by default
extended with the whitespace and comments around the nodes, and applies them with a `Rewriter`.

`rewriter.py` defines the rewriter. A replacement that starts inside the range of an earlier one is appended to it, and a
position outside the content means its end.

`core.rewrite` imports `core.match`, `core.model` and `core.navigate`.

## Related features

- [Rewrite semantics](../../../user/features/rewrite_semantics.md)

## Related concepts

- [Rewrite](../../../user/core/rewrite.md)
- [Rewrite semantics](../../../user/concepts/rewrite_semantics.md)

## Validated by test modules

`test/unit/core/rewrite/`

## Extension points

None: the rewriter works on bytes, whatever the language of the code.

## Non-goals

Finding what to change, which is the task of the matcher.

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.rewrite.rewriter

{ #codemod-core-rewrite-rewriter }

**Stable ID:** `CODEMOD-CORE-REWRITE-REWRITER`

## Responsibility

Replacing byte ranges of a content.

## Location

`src/renaissance/core/rewrite/rewriter.py`

## Public entry points

`renaissance.core.rewrite` exports:

- `Rewriter(content)`: collects replacements of byte ranges of `content`; `replace(start, end, new_content)` adds one, and
  `apply()` returns the content with all of them applied;
- `Rewrite`: one pending replacement: a byte range and its new content.

## Internal structure

A replacement that starts inside the range of an earlier one is appended to it, and a position outside the content means its
end.

## Validated by test modules

- `test/unit/core/rewrite/test_rewriter.py`

## Related concepts

- [Rewrite](../../../user/core/rewrite/rewrite.md)

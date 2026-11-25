<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.syntax_node

{ #codemod-core-model-syntax-node }

**Stable ID:** `CODEMOD-CORE-MODEL-SYNTAX-NODE`

## Responsibility

The protocol of a node of a syntax tree that is a text segment.

## Location

`src/renaissance/core/model/syntax_node.py`

## Public entry points

`renaissance.core.model` exports `SyntaxNode`.

## Internal structure

`SyntaxNode` is defined in terms of `TextSegment` of [`text_segment`](text_segment.md).

## Validated by test modules

- `test/unit/core/model/test_syntax_node.py`

## Related concepts

- [Core model](../../../user/core/model/model.md)

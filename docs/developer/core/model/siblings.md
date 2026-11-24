<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.siblings

{ #codemod-core-model-siblings }

**Stable ID:** `CODEMOD-CORE-MODEL-SIBLINGS`

## Responsibility

The protocol of a contiguous range, or slice, of sibling syntax nodes.

## Location

`src/renaissance/core/model/siblings.py`

## Public entry points

`renaissance.core.model` exports `Siblings`.

## Internal structure

`Siblings` is a text segment of syntax nodes: it is defined in terms of `TextSegment` of [`text_segment`](text_segment.md) and
`SyntaxNode` of [`syntax_node`](syntax_node.md).

## Validated by test modules

None yet.

## Related concepts

- [Core model](../../../user/core/model/model.md)

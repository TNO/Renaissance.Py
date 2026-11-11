<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core model

{ #codemod-core-model }

**Stable ID:** `CODEMOD-CORE-MODEL`

## Responsibility

The vocabulary and structure of syntax tree nodes that every parser binding provides and every generic algorithm consumes.

## Location

`src/renaissance/core/model/`

## Public entry points

The `__all__` of `renaissance.core.model`; see the [API reference](../../api/core/model.md).

- `NodeProtocol`: the structural interface of a node. It extends `NodeNavigateProtocol` of
  [`core.navigate`](navigate.md).
- `SemanticKind`: the language-independent classification of a node.
- `TextSegment`: a consecutive piece of a text, with its offsets, lines and columns.
- `SyntaxNode`: a node of a syntax tree that is a text segment.
- `Siblings`: a contiguous range, or slice, of sibling syntax nodes, which is a text segment too.
- `TextUtils`: shifting, indenting and writing source text.
- `traverse`: a node and all its descendants, breadth first.

`renaissance.core.model.for_bindings` holds what only parser bindings need, to implement node equality (`match_props`,
`match_children`) and node display (`format_node`).

## Internal structure

- `semantic_kind.py` defines `SemanticKind`.
- `node_protocol.py` defines `NodeProtocol`, in terms of `SemanticKind` and `NodeNavigateProtocol`.
- `text_segment.py` defines `TextSegment`.
- `syntax_node.py` defines `SyntaxNode`, and `siblings.py` defines `Siblings`, both in terms of `TextSegment`.
- `text_utils.py` defines `TextUtils`.
- `node_utils.py` defines `traverse`, and the internal `process_node` and `display_context`, which sets whether nodes are
  displayed with their parser kind.
- `for_bindings.py` defines the helpers for parser bindings.

## Related features

- [Parsing and AST access](../../../user/features/parsing_and_ast_access.md)

## Related concepts

- [Core model](../../../user/core/model.md)

## Validated by test modules

`test/unit/core/model/`

## Extension points

A parser binding implements `NodeProtocol` and maps its parser kinds onto `SemanticKind`; see
[Parser and AST modules](../parser_and_ast.md#node-contract).

## Non-goals

`SemanticKind` is a coarse, shared vocabulary, not a universal language taxonomy.

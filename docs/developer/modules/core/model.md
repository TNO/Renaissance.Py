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
- `ASTNode`: the abstract base class of the nodes of the clang bindings, with `ASTReference`, a reference between two
  nodes, and `VisitorResult`, which tells a traversal how to continue.
- `ASTFactory`: creates the nodes of one node class from a file or a text.
- `find_nodes`, `matches_node` and `find_semantic_kind`, also as static methods of `ASTFinder`: the nodes that satisfy a
  predicate or have a semantic kind.
- `ASTShower`: renders a tree of nodes for debugging, with `Displayable`, the shape of a node that it renders.

`renaissance.core.model.format` holds `format_node`, the display of a node, with which the core and the parser bindings
implement `__repr__`.

## Internal structure

- `semantic_kind.py` defines `SemanticKind`.
- `node_protocol.py` defines `NodeProtocol`, in terms of `SemanticKind` and `NodeNavigateProtocol`.
- `text_segment.py` defines `TextSegment`.
- `syntax_node.py` defines `SyntaxNode`, and `siblings.py` defines `Siblings`, both in terms of `TextSegment`.
- `text_utils.py` defines `TextUtils`.
- `node_utils.py` defines `traverse`, and the internal `process_node` and `display_context`, which sets whether nodes are
  displayed with their parser kind.
- `format.py` defines `format_node`, in terms of `display_context`.
- `ast_node.py` defines `ASTNode`, `ASTReference` and `VisitorResult`, in terms of `NodeProtocol`, `format_node` and
  `process_node`.
- `ast_factory.py` defines `ASTFactory`, in terms of `ASTNode`.
- `ast_finder.py` defines `ASTFinder` and its functions, in terms of `NodeProtocol` and `traverse`.
- `ast_shower.py` defines `ASTShower` and `Displayable`, in terms of `display_context`.

The modules import each other from their module, not from the package, so that importing the package imports no module
halfway.

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

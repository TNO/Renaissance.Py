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

- `NodeProtocol`: the structural interface of a node.
- `SemanticKind`: the language-independent classification of a node.

## Internal structure

- `semantic_kind.py` defines `SemanticKind`.
- `node_protocol.py` defines `NodeProtocol`, in terms of `SemanticKind`.

## Related features

- [Parsing and AST access](../../../user/features/parsing-and-ast-access.md)

## Related concepts

- [Core model](../../../user/core/model.md)

## Validated by test modules

`test/unit/core/model/`

## Extension points

A parser binding implements `NodeProtocol` and maps its parser kinds onto `SemanticKind`; see
[Parser and AST modules](../parser-and-ast.md#node-contract).

## Non-goals

`SemanticKind` is a coarse, shared vocabulary, not a universal language taxonomy.

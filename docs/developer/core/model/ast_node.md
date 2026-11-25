<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.ast_node

{ #codemod-core-model-ast-node }

**Stable ID:** `CODEMOD-CORE-MODEL-AST-NODE`

## Responsibility

The abstract base class of the nodes of the clang bindings, with its traversal and rewrite protocol.

## Location

`src/renaissance/core/model/ast_node.py`

## Public entry points

`renaissance.core.model` exports:

- `ASTNode`: the abstract base class;
- `ASTReference`: a reference between two nodes;
- `VisitorResult`: what tells a traversal how to continue.

## Internal structure

`ASTNode` is defined in terms of `NodeProtocol` of [`node_protocol`](node_protocol.md), `format_node` of
[`format`](format.md) and `process_node` of [`node_utils`](node_utils.md).

## Validated by test modules

None yet.

## Related concepts

- [Core model](../../../user/core/model/model.md)

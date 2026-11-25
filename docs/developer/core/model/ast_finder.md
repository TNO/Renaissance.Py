<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.ast_finder

{ #codemod-core-model-ast-finder }

**Stable ID:** `CODEMOD-CORE-MODEL-AST-FINDER`

## Responsibility

Finding the nodes of a tree that satisfy a predicate or have a semantic kind.

## Location

`src/renaissance/core/model/ast_finder.py`

## Public entry points

`renaissance.core.model` exports:

- `find_nodes` and `find_semantic_kind`: the nodes that satisfy a predicate or have a semantic kind;
- `matches_node`: whether a node satisfies a predicate;
- `ASTFinder`: static methods that find the nodes for which a function returns `True` or that it yields (`find_all`), or
  whose parser kind matches a pattern (`find`, `matches_kind`).

## Internal structure

The functions and `ASTFinder` are defined in terms of `ASTNode` of [`ast_node`](ast_node.md), `NodeProtocol` of
[`node_protocol`](node_protocol.md) and `traverse` of [`node_utils`](node_utils.md).

## Validated by test modules

- `test/unit/core/model/test_ast_finder___parsed_c.py`
- `test/unit/core/model/test_ast_finder___predicate.py`
- `test/unit/core/model/test_ast_finder___semantic_kind.py`

## Related concepts

- [Core model](../../../user/core/model/model.md)

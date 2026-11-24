<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.ast_shower

{ #codemod-core-model-ast-shower }

**Stable ID:** `CODEMOD-CORE-MODEL-AST-SHOWER`

## Responsibility

Rendering a tree of nodes for debugging.

## Location

`src/renaissance/core/model/ast_shower.py`

## Public entry points

`renaissance.core.model` exports:

- `ASTShower`: renders a tree of nodes;
- `Displayable`: the shape of a node that it renders.

## Internal structure

`ASTShower` is defined in terms of `display_context` of [`node_utils`](node_utils.md).

## Validated by test modules

None yet.

## Related concepts

- [Core model](../../../user/core/model/model.md)

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.node_utils

{ #codemod-core-model-node-utils }

**Stable ID:** `CODEMOD-CORE-MODEL-NODE-UTILS`

## Responsibility

The traversal of a tree, and the setting whether nodes are displayed with their parser kind.

## Location

`src/renaissance/core/model/node_utils.py`

## Public entry points

`renaissance.core.model` exports `traverse`: a node and all its descendants, breadth first.

## Internal structure

The module also defines the internal `process_node`, which [`ast_node`](ast_node.md) uses, and `display_context`, which
sets whether nodes are displayed with their parser kind, and which [`format`](format.md) and [`ast_shower`](ast_shower.md)
use.

## Validated by test modules

None yet.

## Related concepts

- [Core model](../../../user/core/model/model.md)

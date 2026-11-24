<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.node_protocol

{ #codemod-core-model-node-protocol }

**Stable ID:** `CODEMOD-CORE-MODEL-NODE-PROTOCOL`

## Responsibility

The structural interface of a node, which every parser binding provides and every generic algorithm consumes.

## Location

`src/renaissance/core/model/node_protocol.py`

## Public entry points

`renaissance.core.model` exports `NodeProtocol`.

## Internal structure

`NodeProtocol` is defined in terms of `SemanticKind` of [`semantic_kind`](semantic_kind.md), and extends
`NodeNavigateProtocol` of [`core.navigate.protocols`](../navigate/protocols.md).

## Validated by test modules

- `test/unit/core/model/test_node_protocol.py`

## Related concepts

- [Core model](../../../user/core/model/model.md)

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.navigate.navigate

{ #codemod-core-navigate-navigate }

**Stable ID:** `CODEMOD-CORE-NAVIGATE-NAVIGATE`

## Responsibility

The ancestors and siblings of a node.

## Location

`src/renaissance/core/navigate/navigate.py`

## Public entry points

`renaissance.core.navigate` exports:

- `is_ancestor_of`, `is_proper_ancestor_of`, `ancestors` and `proper_ancestors`: the ancestors of a node;
- `nearest_ancestor` and `nearest_proper_ancestor`: the nearest ancestor of a node for which a predicate holds;
- `next_sibling` and `previous_sibling`: the node after or before a node in the children of its parent.

## Internal structure

The functions are defined in terms of the protocols of [`protocols`](protocols.md). The terms and the decisions behind them
are in [Navigation of code](../../architecture/navigation.md).

## Validated by test modules

- `test/unit/core/navigate/test_navigate.py`

## Related concepts

- [Navigate](../../../user/core/navigate/navigate.md)

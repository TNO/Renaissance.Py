<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Core navigate

{ #codemod-core-navigate }

**Stable ID:** `CODEMOD-CORE-NAVIGATE`

## Responsibility

The navigation of a syntax tree: the protocols a node implements to be navigated, and the ancestors and siblings of a node.

## Location

`src/renaissance/core/navigate/`

## Public entry points

The `__all__` of `renaissance.core.navigate`; see the [API reference](../../api/core/navigate.md).

- `HasParent`, `HasChildren` and `NodeNavigateProtocol`: the navigation protocols.
- `is_ancestor_of`, `is_proper_ancestor_of`, `ancestors` and `proper_ancestors`: the ancestors of a node.
- `nearest_ancestor` and `nearest_proper_ancestor`: the nearest ancestor of a node for which a predicate holds.
- `next_sibling` and `previous_sibling`: the node after or before a node in the children of its parent.

The terms and the decisions behind them are in [Navigation of code](../../architecture/navigation.md).

## Internal structure

- `protocols.py` defines the navigation protocols.
- `navigate.py` defines the functions, in terms of the protocols.

`core.navigate` imports nothing from the rest of the core: it is the lowest core layer, below `core.model`.

## Related features

- [Navigation](../../../user/features/navigation.md)

## Related concepts

- [Navigation](../../../user/core/navigate.md)

## Validated by test modules

`test/unit/core/navigate/`

## Extension points

A parser binding implements `NodeNavigateProtocol`, which `NodeProtocol` extends; the functions then work on its nodes.

## Non-goals

Navigation by usage, such as from a reference to its definition, and by inheritance, which depend on the parser binding.

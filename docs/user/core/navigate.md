<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Navigate

{ #concept-core-navigate }

**Stable ID:** `CONCEPT-CORE-NAVIGATE`

## Purpose

Describe how to move through a syntax tree: up to the ancestors of a node, and down to its children. The siblings of a node
are found by going up to its parent and down to the parent's children.

## Scope

The navigation of the nodes whose parser binding provides the navigation protocols, whatever the language of the source code.

## Definition

- An **ancestor** of a node is the node itself or an ancestor of its parent. A **proper ancestor** is an ancestor other than
  the node itself.
- `is_ancestor_of(ancestor, node)` and `is_proper_ancestor_of(ancestor, node)` tell whether one node is an ancestor of
  another.
- `ancestors(node)` returns the node, its parent, and so on up to the root. `proper_ancestors(node)` returns the same without
  the node.
- `nearest_ancestor(node, predicate)` returns the first of the ancestors for which the predicate is true, or `None`.
  `nearest_proper_ancestor(node, predicate)` does the same for the proper ancestors. For example,
  `nearest_proper_ancestor(node, lambda ancestor: ancestor.semantic_kind is SemanticKind.FUNCTION)` returns the function
  that contains the node.
- `next_sibling(node)` and `previous_sibling(node)` return the sibling directly after or before the node in the children of
  its parent, or `None`.
- A range, or slice, of siblings is not a node. Its ancestors are those of its parent: `ancestors(siblings.parent)`.

## Invariants / guarantees

- Nodes are compared by identity: two nodes with the same structure at different places in the tree are different nodes.
- The root has no parent and no siblings, and is its only ancestor.

## Related features

- [Navigation](../features/navigation.md)

## Related tests

`test/unit/core/navigate/`

## Related code

`src/renaissance/core/navigate/`

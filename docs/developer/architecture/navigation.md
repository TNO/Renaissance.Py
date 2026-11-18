<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Navigation of code

{ #dev-architecture-code-navigation }

**Stable ID:** `ARCH-CODE-NAVIGATION`

## Ancestors and descendants

If node A contains node B in the AST at any depth — including when A and B are the same node —
then A is an **ancestor** of B and B is a **descendant** of A.

We use the terms *proper ancestor* and *proper descendant* to exclude the node itself.

### Navigation Functionality

* AST structure
    * Parent & Ancestors
    * Children & Descendants
    * Siblings
* Usage
    * definition / (forward) declaration - references (ONLY in current file / analysis unit)
* Inheritance
    * Base - Derived classes

## Shared and adapter navigation

[`core.navigate`](../modules/core/navigate.md) provides the navigation of the AST structure for the nodes that provide its
protocols.

### Protocols

* `HasParent` provides `parent`, typed `Self | None`: the way up the tree. It is `None` at the root.
* `HasChildren` provides `children`, a sequence in source order: the way down the tree.
* `NodeNavigateProtocol` combines them.

When a parser binding lets its nodes provide a protocol, the functions that need it become available for these nodes.

The members are read-only properties, so the protocols stay covariant.
`NodeProtocol` extends `NodeNavigateProtocol`, and the rewriter's `Rewritable` extends `HasParent`: `ASTRewriter` needs only
the upward navigation to order and apply edits.

### Functions

* `is_ancestor_of` and `is_proper_ancestor_of`, `ancestors` and `proper_ancestors`, need only `HasParent`.
* `nearest_ancestor` and `nearest_proper_ancestor` return the first of `ancestors(node)` or of `proper_ancestors(node)` for
  which a predicate is true, or `None`. They need only `HasParent`.
* `next_sibling` and `previous_sibling` return the sibling directly after or before a node, or `None`, including at the root.
  They go up with `parent`, down with `children`, and take the position after or before the node in the sequence that
  `children` returns. So they need `NodeNavigateProtocol`.

Every function compares nodes by identity (`is`), never by equality: node equality is structural, so a node at another place
in the tree that happens to be equal is a different node.

Adapters may provide further navigation helpers, such as `root`, for recipes that need them; their implementation remains
adapter-owned. Their `next_sibling` and `previous_sibling` properties, and `ASTNode.get_ancestor`, delegate to
`core.navigate`.

### Decisions

* Protocol names are verbs, after what the protocol enables, as the names of the core sub-packages are; see
  [Repository structure](repository_structure.md#core). Hence `NodeNavigateProtocol` and `core.navigate`.
* The protocols live in `core.navigate`, with the functions that need them, as `Rewritable` lives with the rewriter. They
  cannot live in `core.model` while the functions are in `core.navigate`: `ASTNode`, which belongs to the model, delegates
  to the functions, so the two packages would import each other. `core.navigate` imports nothing from the rest of the core,
  so it is the lowest core layer, below `core.model`.
* `previous_sibling` and `next_sibling` are a symmetric pair, as are *preceding* and *following*; `preceding_sibling` is not
  used.
* `nearest_ancestor` and `nearest_proper_ancestor` take a predicate rather than a kind. The predicate states its own
  requirement on the node, such as a `parser_kind` or a `semantic_kind`, so `core.navigate` needs no other protocol and does
  not decide how a kind matches.
* `Siblings`, the range of sibling syntax nodes, keeps its name; *slice* is a synonym for *range*.
* `Siblings` implements neither `HasParent` nor `HasChildren`:
    * its `parent` is a node, never `None`, even when the range is empty;
    * an ancestor is a single node, not a slice of nodes, so a slice is never its own ancestor and the distinction between
      ancestor and proper ancestor makes no difference for it. The functions take a node; code that needs the ancestors of
      `Siblings` calls them on `siblings.parent`;
    * the children of the individual siblings have different parents, so together they are not the children of any one node.

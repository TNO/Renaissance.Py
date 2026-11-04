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

`NodeProtocol` guarantees parent and child traversal, so generic algorithms can
navigate ancestors, descendants and siblings; `preceding_sibling` and
`next_sibling` in `renaissance.utils.ast_utils` are shared by all adapters.
`ASTRewriter` requires `Rewritable.parent` for the upward navigation needed to
order and apply edits. Adapters may provide further navigation helpers, such as
`root`, for recipes that need them. Their implementation remains adapter-owned.

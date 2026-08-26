{ #dev-architecture-code-navigation }
# Navigation of code

**Stable ID:** `ARCH-CODE-NAVIGATION`

## Ancestors and descendants

If node A contains node B in the AST at any depth — including when A and B are the same node — then A is an **ancestor** of B and B is a **descendant** of A.

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
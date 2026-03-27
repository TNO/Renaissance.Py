# 01 - Children and properties

Status: Accepted

Date: 2026-02-25

Authors: 
 - jinmin.hu@capgemini.com
 - huub.joosten@capgemini.com
 - luna.li@capgemini.com
 - paul.nelissen@esi.nl
 - pierre.vandelaar@tno.nl

## Context

This document explains the design decision to have all AST nodes contain both children and properties.
Children represent nodes directly connected to a parent node; properties are attributes that describe the node itself.
Having both allows consistent representation of complex structures, simplifies traversal, and separates
structure (children) from node metadata (properties).

## Decision

All AST nodes will expose both children and properties. Children will be represented as an immutable sequence (tuple)
of child nodes. Properties will be stored in an immutable mapping-like structure or as read-only attributes.
Implementations should provide clear accessors for both concepts and prefer non-mutating operations.

## Implementation notes

- Represent children as tuples to convey immutability intent.
- Expose properties through read-only attributes, dataclass frozen fields, or a mapping-like API.
- Provide helper methods for creating modified copies (e.g., `replace`, `copy_with`, or `with_children`).
- Keep the distinction between structural relationships (children) and descriptive data (properties)
  explicit in APIs and documentation.

## example

```python
class GoAstNode:
    @property
    def properties(self) -> dict[str, Any]:
        ...

    @property
    def children(self) -> list[Self]:
        ...

```

## Rationale

This separation makes the AST easier to reason about, enables targeted transformations (structure vs. metadata),
and supports immutability and sharing strategies.

## Consequences

Positive:
- Clearer APIs and traversal logic.
- Easier targeted refactorings and transformations.

Negative:
- Slight overhead in defining and maintaining two parallel concepts.

## Alternatives considered

- Merge children and properties into a single list of mixed entries — rejected because it complicates
  traversal and semantic clarity.

## considered

order of the list matters here and if possible follows the definition in signature text

## Related decisions

- See ADR 04 (Make nodes immutable) for related choices about immutability.

---

Revision history:
- 2026-02-25: Converted to ADR template and clarified decision.

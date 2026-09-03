# 01 - Children and properties

Status: Accepted

Date: 2026-02-25

Authors:

- jinmin.hu@capgemini.com
- huub.joosten@capgemini.com
- luna.li@capgemini.com
- paul.nelissen@esi.nl
- pierre.vandelaar@tno.nl

## Table of contents

- [Context](#context)
- [Decision](#decision)
- [Implementation notes](#implementation-notes)
- [Example](#example)
- [Rationale](#rationale)
- [Consequences](#consequences)
- [Alternatives considered](#alternatives-considered)
- [Related decisions](#related-decisions)

## Context

The goal of this ADR is to define a design that minimize the implementation time of the matching
algorithm when creating renaissance for a new language

This document explains the design decision to have all AST nodes contain both children and properties.
Children represent nodes directly connected to a parent node; properties are attributes that describe the
node itself. Having both allows consistent representation of complex structures, simplifies traversal, and
separates structure (children) from node metadata (properties).

## Decision

All AST nodes will expose both children and properties. Children will be represented as a sequence
of child nodes. Properties will be stored in a map. Implementations should provide clear accessors
for both concepts.

## Implementation notes

- Expose properties through map(dict in Python).
- Provide helper methods for navigating and match.
- Keep the distinction between structural relationships (children) and descriptive data (properties)
  explicit in APIs and documentation.
- The order of the children list matters and should, where possible, follow the order of parameters in the
  node's constructor or grammar production rule.

## Example

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

This separation makes the AST easier to reason about, enables targeted transformations (structure vs.
metadata), and supports sharing strategies.

## Consequences

Positive:

- Clearer APIs and traversal logic.
- Easier targeted refactorings and transformations.

Negative:

- Slight overhead in defining and maintaining two parallel concepts.

## Alternatives considered

- Merge children and properties into a single list of mixed entries — rejected because it complicates
  traversal and semantic clarity.

## Related decisions

- See ADR 04 (Make nodes immutable) for related choices about immutability.

---

Revision history:

- 2026-02-25: Converted to ADR template and clarified decision.
- 2026-03-27: Added table of contents; moved ordering note into Implementation notes;
  renamed Example section to match template.

# 04 - Make nodes immutable

Status: Proposal

Date: 2026-02-25



## Context

The project models trees made of nodes. Currently, node data (properties and children) is conceptually considered
stable: most operations read the tree and transformations create new trees instead of mutating in-place.
Ensuring immutability helps reasoning about transformations, enables safer concurrency, and opens opportunities
for caching and memoization.

## Decision

Nodes will be implemented as immutable objects. Once a node is created, its properties and children cannot be
modified. Any change to a tree (for example, updating a property or replacing a child) will produce a new node
(or subtree) rather than mutating the existing node in-place.

Implementation notes and recommendations for contributors:

- Use language features and patterns that express immutability clearly. In Python this can mean:
  - dataclasses with frozen=True, or
  - plain classes exposing only read-only properties, and storing children in tuples instead of lists, or
  - namedtuple / typing.NamedTuple for simple node shapes.
- Provide helper/builder functions or factory methods to create modified copies of nodes
  (for example, a `with_*` method or `replace`/`copy_with` pattern that returns a new node with the requested
  changes).
- When storing child collections, prefer immutable sequences (tuples) to make intent explicit and prevent
  accidental mutation.
- Consider shallow and structural sharing where safe: reuse unchanged subtrees to reduce allocation and improve
  performance.

## Rationale

- Predictability: Callers can rely on a node's properties remaining the same after construction,
  simplifying reasoning about passes and refactorings.
- Concurrency: Immutable data structures are safe to share across threads without synchronization.
- Caching & memoization: Since nodes don't change, caching derived information (like computed hashes,
  string representations, or analysis results) is reliable.
- Correctness: Avoids accidental side effects caused by in-place modifications during complex refactorings.

```python
    @property
    def properties(self) -> dict[str, int | str]:
        return {"name": self.name}

    @property
    def children(self) -> list[Self]:
        return [
            self.expr,
            self.body,
            self.other,
        ]

```

## Consequences

Positive:
- Easier reasoning about code that manipulates trees.
- Safer concurrent processing and simplified caching.
- Fewer bugs due to unintended mutation.

Negative / trade-offs:
- Potential performance overhead due to allocation when creating modified copies.
  Mitigations include structural sharing (reusing unchanged children) and keeping node representations compact.
- Some algorithms that expect in-place updates will need to be adapted or re-implemented in an immutable style.
- Developers must learn and follow patterns for producing modified copies (builders, `copy_with` helpers).

## Alternatives considered

1. Mutable nodes with defensive copies
   - Keep nodes mutable but perform defensive copying when necessary.
   - Rejected because it is easy to forget copies and still produce subtle bugs.

2. Hybrid approach: mostly immutable, but allow controlled mutation through explicit APIs
   - Provides flexibility but complicates invariants and testing; increases cognitive load.

3. Fully persistent immutable data structures (e.g., ropes, HAMT, custom persistent vectors)
   - Strong sharing and performance but larger implementation cost and complexity;
     deferred for future optimization if needed.

## Related decisions

- See ADR 01 (children and properties) and ADR 02 (direct access) for related design choices about tree shape
  and access patterns.


---

Revision history:
- 2026-02-25: Draft; adds ADR template and implementation guidance.

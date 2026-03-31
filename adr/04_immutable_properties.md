# 04 - nodes can be immutable

Status: Proposal

Date: 2026-02-25



## Context

The project models trees made of nodes. Currently, node data (properties and children) most operations read the 
tree and transformations create new trees instead of mutating in-place. Ensuring immutability helps reasoning 
about transformations, enables safer concurrency, and opens opportunities for caching and memoization.

## Decision

Nodes can be implemented as immutable objects. Once a node is created, its properties and children cannot be
modified. Any change to a tree (for example, updating a property or replacing a child) will be done through a rewriter 
produce a new node valid rather than mutating the existing node in-place.

Implementation notes and recommendations for contributors:

- Provide rewriter to create modified copies of nodes  (for example, a `replace`, `remove` `insert`
  pattern that returns a new node with the requestedchanges).
- When storing modifications, make sure the result is still correct and raise exception in case of unsulvable conflict.

## Rationale

- Predictability: Callers can rely on a node's properties remaining the same after construction,
  simplifying reasoning about passes and refactorings.
- Concurrency: Immutable data structures are safe to share across threads without synchronization.
- Caching & memoization: Since nodes don't change, caching derived information (like computed hashes,
  string representations, or analysis results) is reliable.
- Correctness: Avoids accidental side effects caused by in-place modifications during complex refactorings.

```python
    # no problem
    rewrite.replace(new_contetent, ast.child[1:3])    
    # can bea problem because the line number chenged, but it is solvable
    rewrite.replace(new_contetent, ast.child[4:6])    
    
    # reaise exception, because it is partly changed end not gerantteed the result is still sytactical correct
    rewrite.replace(new_contetent, ast.child[2:4])

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

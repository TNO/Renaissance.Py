# 05 - Use Python's built-in dunder methods for node behavior

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
- [Rationale](#rationale)
- [Consequences](#consequences)
- [Alternatives considered](#alternatives-considered)
- [Related decisions](#related-decisions)


## Context

The goal of this ADR is to create an implementation of renaissance that feels native to the python world and reduce 
the verbosity without misusing the original meanings.

Nodes should integrate naturally with Python idioms and be easy to inspect, compare, iterate, and hash when
appropriate. Using Python's special methods (``__repr__``, ``__eq__``, ``__hash__``, ``__str__``, ``__len__``,
``__iter__``, ``__getitem__``, ``__contains__``, etc.) gives predictable, idiomatic behavior.

## Decision

Implement and document a small, consistent set of dunder methods on node types to enable common operations.
Not every node must implement every method — choose the methods that make sense for the node's semantics
(for example, sequence-like nodes should implement ``__len__`` and ``__iter__``).

## Implementation notes

- ``__repr__``: Provide an unambiguous, developer-oriented representation useful for debugging and display (ASTShower). 
- ``__str__``: Provide a readable representation intended for users or logs.
- ``__eq__`` and ``__hash__``: Implement equality of ASTNodes are logically value-like
  and immutable (see ADR 04). If nodes are mutable or identity matters, prefer identity-based equality and
  avoid making them hashable.
- ``__len__`` / ``__iter__`` / ``__getitem__``: Implement for sequence-like node types to allow Pythonic
  iteration and indexing. witch maps to children in our case.
- ``__contains__``: Implement if membership semantics are meaningful.
- Avoid surprising side effects in any dunder method. Keep them simple and consistent.
    `AST Node != AST Pattern`

```python

class GoAstNode:

# easier to see in debugger and it is used in astshower
def __repr__(self) -> str:
    return f"{type}....."

#shorthand for nth children
__getitem__(self, index) -> Self:
    return self.children[index]
```

## Rationale

- Idiomatic usage: makes nodes easier to use with Python language features and libraries.
- Debuggability: ``__repr__`` and ``__str__`` improve developer experience.
- Interoperability: sequence and mapping protocols let nodes interoperate with Python collection utilities.

## Consequences

Positive:
- More predictable developer experience and easier debugging.
- Better interoperability with Python tools and libraries.

Negative:
- Risk of over-implementing dunder methods and creating surprising behavior;
  prefer conservative, well-documented choices.

## Alternatives considered

- Minimal API surface with no special methods — rejected because it reduces ergonomics.

## Related decisions

- See ADR 04 (Make nodes immutable) when implementing ``__hash__`` and ``__eq__``.

## note

is_match is __not the same as __eq__
also it avoids extra implementation 

---

Revision history:
- 2026-02-25: Converted to ADR template and clarified decision.

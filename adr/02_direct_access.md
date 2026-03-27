# 02 - Direct access to fields

Status: Accepted

Date: 2026-02-25


Authors: 
 - jinmin.hu@capgemini.com
 - huub.joosten@capgemini.com
 - luna.li@capgemini.com
 - paul.nelissen@esi.nl
 - pierre.vandelaar@tno.nl
## Context

Direct access refers to exposing node fields and attributes using a Pythonic style (e.g., `_fields`, `_attributes`) rather than using explicit accessor methods such as `get_children()` or `get_children`. This allows for natural attribute access, simpler metaprogramming, and compatibility with Python tooling and idioms.

## Decision

Adopt a Pythonic direct-access convention for node definitions. Nodes may declare a `_fields` or `_attributes` tuple (as in CPython's `ast` module) that names structural fields. Consumers and tools should read these fields rather than relying on bespoke accessor methods. Implementations should still provide stable, documented APIs for traversal and transformation.

## Implementation notes

- Follow patterns used by CPython's `ast` module (using `_fields` for structural fields).
- Keep a clear mapping between `_fields` and how children/properties are stored internally.
- Provide compatibility helper functions to convert between direct-access style and other APIs when needed.


```python
class GoAstNode:
    #direct access protocol
    expr:Self
    body:Sequence[Self]
    other:Sequence[self]
    
    #rewrite protocol
    length:int
    offset:int
    name:str

    #matcher
    properties:dict[str, int | str] ={
        "length": length,
        "offset": offset,
        "name": name
    }
    children:list[Self] = [expr, body, other]

```
## Rationale

Using Python conventions reduces boilerplate, makes code easier to inspect and manipulate, and aligns with developer 
expectations in a Python project.

## Consequences

Positive:
- Lower boilerplate and clearer node definitions.
- Easier integration with Python tooling.

Negative:
- Slight coupling to Python conventions; if we port the model to other languages some idioms will differ.

## Alternatives considered

- Exclusive use of accessor methods — rejected because it increases verbosity and reduces interop with Python tooling.

## Related decisions

- See ADR 01 (Children and properties) and ADR 04 (Make nodes immutable).

---

Revision history:
- 2026-02-25: Converted to ADR template and clarified decision.

# 03 - Duck typing for nodes

Status: Accepted

Date: 2026-02-25

Authors: 
 - jinmin.hu@capgemini.com
 - huub.joosten@capgemini.com
 - luna.li@capgemini.com
 - paul.nelissen@esi.nl
 - pierre.vandelaar@tno.nl

## Context

The goal of this ADR is to minimize the implementation of ASTNode for a new language while still taking advantage 
of the generic algorithms

The project is implemented in Python and must remain flexible in how AST-like nodes are represented.
Rather than enforcing a strict class hierarchy, we want code that accepts any object that looks and behaves like a
node (has required properties and children). This is the essence of duck typing.

## Decision

Treat nodes by behavior (structural and API shape) rather than by explicit concrete types.
A value is considered a valid node if it exposes the required fields, properties, and child access patterns
expected by the consumers.

## Implementation notes

- Document the node "shape" that consumers rely on
  (e.g., required attribute names, `_fields` tuple, iteration semantics, and read-only accessors).
- Use structural typing where helpful: Python protocols (`typing.Protocol`) can express expected attributes
  and aid static type checkers (mypy/pyright).
- Add runtime assertions or light validation at public API boundaries where robustness is important
  (for example, when importing external nodes or plugin-provided nodes).
- Keep core algorithms defensive: prefer attribute access with sensible fallbacks rather than brittle type checks.
- Provide adapter/wrapper helpers (see ADR 06) to normalize foreign node-like objects into the project's
  canonical node shape.

```python
@runtime_checkable
class NodeMatchProtocol(protocol):
    properties: dict
    children: list[Self]

def is_match(src: NodeMatchProtocol, cmp: NodeMatchProtocol) -> bool:
    ...
```

## Rationale

- Flexibility: allows integrating nodes produced by different parsers or external tools without heavy wrapper work.
- Simplicity: avoids deep inheritance trees when behavior is all that's required.
- Interoperability: easier to write adapters and tests against small, focused protocols.

## Consequences

Positive:
- Easier integration with third-party node representations.
- Reduced boilerplate for small, local node-like objects used in tests.

Negative:
- Potential for runtime errors if an object only partially implements the expected shape;
  mitigated by runtime checks at boundaries and clear documentation.
- Slightly looser guarantees than strict nominal typing.

## Alternatives considered

- Enforce a strict base node class — rejected for flexibility reasons.
- Rely solely on runtime duck checks with no static typing — rejected in favor of combining runtime checks
  with Protocols for better tooling.

## Comment and whitespace

comment and white space belongs to astnode.
is comment need to it own property without "comment sign"

## Related decisions

- See ADR 06 (Wrapper or adapter) and ADR 01 (Children and properties).


---

Revision history:
- 2026-02-25: Converted to ADR template and clarified decision.

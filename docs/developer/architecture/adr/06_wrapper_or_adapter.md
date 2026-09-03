# 06 - Wrapper or adapter for external node shapes

Status: Proposal

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

The goal of this ADR is to define a strategy for interoperating with external node-like objects that do not
match the project's canonical node shape while minimize the effort for the developer of the new language for renaissance.

The project may receive nodes from different parsers or libraries that do not match the project's canonical node
shape. We need a strategy to interoperate with foreign node-like objects while preserving the project's APIs
and expectations unig minimum amount of code.

## Decision

Prefer writing only the protocol function on top of the current native implementation if not already available.
This requires a minimum amount of implementation and opportunity for reuse of the matcher and rewrite
functionalities.

Thin wrappers (adapter objects) that present the project's canonical node API while delegating to the original
node make behavior explicit, allow normalization, and preserve access to the original node when necessary.

## Implementation notes

- Implement simple wrapper/adaptor classes that implement the project's node Protocol (see ADR 03).
- Keep wrappers thin: delegate attribute and child access where possible and only normalize differences
  that matter.

```Python

# monkey patching the ast node to have properties and children, so that it can be used directly in the matcher and rewriter without needing to write an adapter for it.
@property
def properties(self: AST) -> dict[str, Any]:
    props = {}
    for name in self._fields:
        props[name] = getattr(self, name)
    return props


AST.properties = properties


@property
def children(self: AST) -> list[AST]:
    return getattr(self, "body", [])


AST.children = children

# wrapper example for a foreign node type (e.g., from a third-party parser)

class PythonASTNode:
    def __init__(self, node: ast):
        self._node = node
    @property
    def properties(self):
      return {'name':self._node.name, 'value':self._node.value}
    @property
    def children(self):
        return [PythonASTNode(n) for n in self._node.body]
 
# adapter example    
class PythonASTNode:
  def __init__(self, node):
    self.properties["name"] = self.derive_name_from(node)

```

## Rationale

- Wrappers preserve original semantics and make interop explicit.
- Adapters make it easy to support multiple external sources without changing core logic.

## Consequences

Positive:

- Clear interoperability surface and testable adapters.
- Avoids spreading compatibility code throughout the codebase.

Negative:

- Slight overhead of adapter objects and maintenance of adapter code.

## Alternatives considered

- Modify external objects in place — rejected because it mutates foreign data and can have side effects.
- Copy-and-normalize into internal-only node instances — viable but may be more expensive than thin wrappers.

## Related decisions

- See ADR 03 (Duck typing) and ADR 01 (Children and properties).

---

Revision history:

- 2026-02-25: Converted to ADR template and clarified decision.

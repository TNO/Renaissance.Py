# 06 - Wrapper or adapter for external node shapes

Status: Proposal

Date: 2026-02-25

Authors: Project contributors

## Context

The project may receive nodes from different parsers or libraries that do not match the project's canonical node shape. We need a strategy to interoperate with foreign node-like objects while preserving the project's APIs and expectations.

## Decision

Prefer writing only the protocol function on top of the current native implementation if not already available.
this requires minimum amount of implementation and oppertunity for reuse of the maatcher and rewrite , etc functionalities

'thin wrappers (adapter objects) that present the project's canonical node API while delegating to the original node. Wrappers make behavior explicit, allow normalization, and preserve access to the original node when necessary.'

## Implementation notes

- Implement simple wrapper/adaptor classes that implement the project's node Protocol (see ADR 03).
- Keep wrappers thin: delegate attribute and child access where possible and only normalize differences that matter.
- Provide utility constructors (e.g., `from_external`) and tests for common external formats.
- Consider caching or memoization in adapters if adaptation is expensive.

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

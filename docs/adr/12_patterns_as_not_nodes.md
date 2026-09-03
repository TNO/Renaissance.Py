# 12 - Patterns Are Not Nodes

Status: Proposal

Date: 2026-03-27

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

The goal of this ADR is to clarify the distinction between code factories and pattern factories in the
Renaissance project.

In the current implementation a pattern is just an AST node. This is not desirable: while a pattern may be
realized using an AST node under the hood, it may also carry additional information that has no place in a
plain AST node.

For example, to pattern-match `create_expression('$x')` it is convenient for the pattern to also record the
desired syntactic kind (expression, statement, declaration, …). Without that extra information the correct
kind must be inferred from the surrounding context — which is possible in most cases (as demonstrated by an
earlier prototype) but is fragile and adds complexity to the matcher.

Having a separate `Pattern` type that wraps an AST node and adds metadata makes both the code factory and
the pattern factory first-class concepts with clearly separated responsibilities.

## Decision

Introduce two distinct factory families:

- **Code factories** — turn source-code snippets (given a syntactic context: statement, declaration,
  expression, …) into plain AST nodes.
- **Pattern factories** — create `Pattern` objects that are used for matching. A `Pattern` wraps an AST node
  and additionally records the expected syntactic kind and any other match-time metadata.

A `Pattern` is therefore **not** an AST node; it is a separate value type that holds an AST node together
with matching metadata.

## Implementation notes

- Define a `Pattern` dataclass (frozen) with at least:
  - `node: AstNode` — the template node used for structural matching.
  - `kind: SyntacticKind` — the expected kind (e.g., `EXPRESSION`, `STATEMENT`, `DECLARATION`).
  - Optional: captured variable names, constraints, etc.
- Code factories (`code_factory`) accept a source snippet and a `SyntacticKind` and return an `AstNode`.
- Pattern factories (`pattern_factory`) accept a source snippet with placeholders (e.g., `$x`) and a
  `SyntacticKind` and return a `Pattern`.
- The matcher operates on `Pattern` objects, not raw `AstNode` objects, so it can exploit the stored `kind`
  without re-inferring it from context.

```python
from dataclasses import dataclass
from renaissance.common import AstNode, SyntacticKind

@dataclass(frozen=True)
class Pattern:
    node: AstNode
    kind: SyntacticKind

def code_factory(snippet: str, kind: SyntacticKind) -> AstNode:
    ...

def pattern_factory(snippet: str, kind: SyntacticKind) -> Pattern:
    node = code_factory(snippet, kind)
    return Pattern(node=node, kind=kind)
```

## Example

```python
# Create an AST node for a statement
assignment = code_factory("x = 1", SyntacticKind.STATEMENT)

# Create a pattern that matches any expression assigned to $x
expr_pattern = pattern_factory("$x", SyntacticKind.EXPRESSION)

# The matcher can use expr_pattern.kind directly — no inference needed
matches = matcher.find(tree, expr_pattern)
```

## Rationale

Keeping `Pattern` separate from `AstNode` respects the single-responsibility principle: AST nodes represent
source structure; patterns represent match intent. Encoding the syntactic kind directly in the `Pattern`
eliminates the need for fragile context inference in the matcher and makes pattern creation explicit and
self-documenting. The two factory families mirror this separation cleanly.

## Consequences

Positive:

- Matcher logic is simpler: the expected kind is available directly on the `Pattern`.
- Pattern creation is explicit: callers state the intended kind at the call site.
- AST nodes remain pure structural representations, uncontaminated by matching metadata.
- The two factory families provide a clear, discoverable API surface.

Negative:

- Two factory families must be defined and maintained instead of one.
- Existing code that treats patterns as plain AST nodes must be migrated.

## Alternatives considered

- Reuse `AstNode` as pattern (current approach) — rejected because it conflates structural representation
  with match metadata and requires fragile kind inference in the matcher.
- Subclass `AstNode` to create `PatternNode` — rejected because inheritance couples the pattern type to the
  node hierarchy and still requires carrying extra fields not appropriate for plain nodes.

## Related decisions

- See ADR 01 (Children and properties) for the AST node structure that `Pattern.node` wraps.
- See ADR 03 (Duck typing) for the protocol-based approach used by the matcher to accept `Pattern` objects.
- See ADR 10 (Type hierarchy) for the `SyntacticKind` taxonomy used as the `kind` field.

---

Revision history:

- 2026-03-27: Converted to ADR template and clarified decision.

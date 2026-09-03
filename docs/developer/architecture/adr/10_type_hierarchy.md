# 10 - Type Hierarchy

Status: Accepted

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

the goal of this ADR is to establish a robust and maintainable type hierarchy for AST nodes use in the algorithms
within the Renaissance project and across the languages.

AST node types are currently identified by string-based type names (e.g., re.compile(kind,
`(?i)Function_?Decl".IGNORECASE)`). This approach is fragile, hard to refactor, and requires every consumer to know the
exact string values. In addition, helper functions such as `is_statement`and `is_expression` must each maintain their
own lookup tables. A class hierarchy provides a more robust and idiomatic solution.

## Decision

- Follow the Doxygen definition for common node types (e.g., statement, expression, declaration) and use native Python
- types for language-specific or non-standard node kinds.
- Use the class hierarchy to determine the type of a node instead of string-based type name comparisons.
- Helper functions such as `is_statement` and `is_expression` will delegate to `isinstance` checks, making them generic
- and significantly simpler.

## Implementation notes

- Define abstract base classes for the common node categories (e.g., `statement`, `expression`,`declaration`) following
  Doxygen terminology.
- Language-specific node kinds that have no Doxygen equivalent are represented as native Python classes inheriting from
  the appropriate base.
- Replace all `node.type == "..."` comparisons with `isinstance(node.type, Statement)` checks.
- Implement helper predicates as thin wrappers:

```python
def is_statement(node: AstNode) -> bool:
    return isinstance(node.kind, Statement)

def is_expression(node: AstNode) -> bool:
    return isinstance(node.kind, Expression)

# Usage
node.kind =Assignment(...)
assert is_statement(node)        # True — no string comparison needed
assert not is_expression(node)   # False
```

## Example

## Rationale

Using the class hierarchy to determine node types is more robust than string comparisons: it is refactor-safe,
IDE-navigable, and benefits from Python's `isinstance` semantics. Following Doxygen's well-known taxonomy for common
node categories ensures consistency with established conventions and makes the codebase accessible to developers
familiar with that terminology. Helper functions become trivially simple and generically applicable across all language
frontends.

## Consequences

Positive:

- Eliminates fragile string-based type comparisons.
- Helper functions (`is_statement`, `is_expression`, …) become simple, generic, and reusable.
- IDE tooling (auto-complete, go-to-definition, refactoring) works naturally with class hierarchies.
- Consistent with Doxygen conventions for common node categories.

Negative:

- Requires an upfront investment to define the class hierarchy and migrate existing string comparisons.
- Deep inheritance trees can become hard to navigate if not kept shallow and well-documented.

## Alternatives considered

- String-based type names — rejected because they are fragile, not refactor-safe, and require consumers to know exact string values.
- Enum-based type tags — rejected because they do not compose well with inheritance and still require explicit lookup tables in helper functions.

## Related decisions

- See ADR 01 (Children and properties) for the overall AST node design that this hierarchy builds upon.
- See ADR 03 (Duck typing) for cases where structural subtyping with `Protocol` is preferred over nominal subtyping.

---

Revision history:

- 2026-03-27: Converted to ADR template and clarified decision.

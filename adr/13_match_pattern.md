# 13 - Match Pattern

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

A match pattern is a source-code snippet that may contain **placeholders** — special names prefixed with `$`
(single node) or `$$` (sequence of nodes). Patterns are used to find and transform code in a language-agnostic
way. Two design questions drive this ADR:

1. **At what AST level should a placeholder match?**
   A placeholder node (an `IASTName`) should match at the *highest* AST node whose concrete syntax reduces
   to a single name, determined by recursively applying `getPlaceholderName`. This lets `$x` in the pattern
   `$x;` match a full expression statement, not just an identifier.

2. **How should repeated placeholders be compared?**
   The same placeholder can be bound to nodes of *different* AST classes within one pattern
   (e.g., `$type* ptr = new $type()` binds `$type` first to `IASTNamedTypeSpecifier`, then to `IASTTypeId`).
   Comparison must therefore be structural (value equality), not class-based.

## Decision

- A placeholder matches at the **highest** AST node whose concrete syntax reduces to a single name
  (function `getPlaceholderName` applied recursively).
- Multiple occurrences of the same placeholder in a pattern express an **equality constraint**: all bound
  nodes must be structurally equal, regardless of their AST class.
- Implicit placeholders must **not** be triggered inside string literals (`"$X"`) or comments (`/* $X */`).
- Sequence placeholders (`$$name`) match zero or more consecutive sibling nodes.
- Patterns support **equivalent code matching**:
  - Readability separators: `1_000_000` ≡ `1000000`
  - Numeric bases: `0xFF` ≡ `255`
  - Scientific notation: `1E2` ≡ `100`
  - String delimiters: `"ape"` ≡ `'ape'`
  - String concatenation: `"con" "cat"` ≡ `"concat"`
  - Symmetric operators: `0 == x` matches `x == 0`
  - Equivalent initialisers (C++): `int x = 1;` matches `int x { 1 };`

## Implementation notes

- Implement `getPlaceholderName(node) -> str | None` recursively: return the placeholder name if the node's
  entire concrete syntax is a single `$`-prefixed name; otherwise return `None`.
- When binding a repeated placeholder, use structural comparison (compare the unparse of each bound node),
  not `isinstance` / class identity.
- Parse patterns in a dedicated syntactic context (statement, expression, declaration) to avoid ambiguity;
  see ADR 12 (Patterns are not nodes) for the `Pattern` + `SyntacticKind` design.
- Sequence placeholders (`$$`) must be matched greedily against sibling lists, subject to the constraints
  of surrounding fixed nodes in the pattern.
- Equivalent-code normalisation is applied before structural comparison; maintain a normalisation table per
  language frontend.

## Example

| Pattern | Matches |
|---------|---------|
| `int $$x;` | `int a=4, b=5, c;` |
| `$type v;` | `const myclass v;` |
| `x = $value;` | `x = 1 + 2;` |
| `$x;` | `a = f(1, 2+3);` |
| `$type* ptr = new $type()` | `MyClass* ptr = new MyClass()` |
| `$f; var = $f;` | `foo(); var = foo();` |

```python
# Placeholder resolution
def get_placeholder_name(node: AstNode) -> str | None:
    """Return the placeholder name if node reduces to a single $-name, else None."""
    if isinstance(node, NameNode) and node.value.startswith("$"):
        return node.value
    children = node.children
    if len(children) == 1:
        return get_placeholder_name(children[0])
    return None

# Structural equality for repeated placeholders
def placeholders_equal(a: AstNode, b: AstNode) -> bool:
    return unparse(a) == unparse(b)
```

## Rationale

Matching at the highest AST node whose syntax reduces to a single name maximises the expressiveness of a
pattern: `$x;` can capture an entire statement, not just a leaf identifier. This was validated by an earlier
CDT-based prototype. Structural (unparse-based) equality for repeated placeholders avoids fragile class
comparisons and handles the known C++ cases where the same placeholder binds to nodes of different classes.

## Consequences

Positive:
- Patterns are expressive: a single placeholder can match complex sub-trees.
- Repeated-placeholder equality is robust across AST class differences.
- Equivalent-code matching reduces the number of patterns needed to cover syntactic variants.

Negative:
- `getPlaceholderName` must be implemented and maintained for each language frontend.
- Structural equality via unparsing may be slower than direct node comparison; caching may be required.
- Equivalent-code normalisation tables must be kept in sync with language specifications.

## Alternatives considered

- Match placeholder at the **lowest** (leaf) AST node — rejected because it prevents `$x` from matching
  expression statements and other compound nodes.
- Use **class-based** equality for repeated placeholders — rejected because the same placeholder can legally
  bind to nodes of different classes in a single pattern (documented C++ cases above).
- Require explicit syntactic kind annotation on every placeholder — rejected because it adds verbosity;
  kind is inferred via `getPlaceholderName` and the surrounding `Pattern.kind`.

## Related decisions

- See ADR 12 (Patterns are not nodes) for the `Pattern` / `SyntacticKind` design used by the pattern
  factory.
- See ADR 10 (Type hierarchy) for the node kind taxonomy referenced by find-by-kind functionality.
- See ADR 08 (Test architecture) for the test requirements that cover matching, placeholders, and
  equivalent-code matching.
- See ADR 11 (Parser with space and comment) for the lossless round-trip required by transformation tests.

---

Revision history:
- 2026-03-27: Converted GitHub issue to ADR template.

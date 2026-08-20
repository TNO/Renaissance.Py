{ #template-architecture }
# Architecture template

**Stable ID:** `TEMPLATE-ARCH`

```md
{ #dev-architecture-<slug> }
# <Architecture topic title>

**Stable ID:** `ARCH-<AREA>-<NAME>`

## Purpose

Document the design decisions that determine how <topic> is implemented.

## Scope

<What this document covers and what it explicitly does not cover.>

## Definition

<Conceptual definition of the topic, if applicable.>

### <Decision topic>

<Context: describe the problem or question that needs to be decided.>

<Options (optional):>
* <Option A>
* <Option B>

**Comparison** *(optional)*

<Trade-offs between the options.>

**Decision**

<The chosen option and the rationale.>

### <Additional decision topic>

<Repeat the structure above for each significant design decision.>

## Invariants / guarantees

* <Observable property that holds as a result of the decisions above.>

## Related features

## Related tests

## Related code

## Notes
```

## Guidance

### When to use this template

Use this template for pages in `docs/developer/architecture/` that record design decisions for a specific topic, subsystem, or workflow step.

### Anchor and stable ID conventions

| Element | Pattern | Example |
|---|---|---|
| Page anchor | `#dev-architecture-<slug>` | `#dev-architecture-code-find` |
| Stable ID | `ARCH-<AREA>-<NAME>` | `ARCH-CODE-FIND` |

The `<AREA>` segment groups related architecture pages (e.g., `CODE`, `TEST`, `PROJECT`).

### Decision sub-sections

Each significant design decision should be its own `###` sub-section under `## Definition`.
The structure within a decision sub-section is:

1. **Context** — plain prose describing the problem or alternatives.
2. **Comparison** *(optional)* — explicit trade-offs when multiple options are viable.
3. **Decision** — bold heading followed by the chosen option and rationale.

### Invariants / guarantees

List observable properties that hold as a direct consequence of the decisions recorded in this document.
These serve as a contract for implementers and reviewers.

### Leaving sections empty

`## Related tests` and `## Related code` may be left empty as placeholders when not yet known.
`## Notes` may be omitted if there is nothing to add.

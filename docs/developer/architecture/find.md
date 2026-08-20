{ #dev-architecture-code-find }
# Find

**Stable ID:** `ARCH-CODE-FIND`

## Purpose

Document the design decisions that determine how the find step is implemented within the find-filter-modify workflow.

## Scope

The find step locates syntactic [matches](../../user/concepts/matching.md) within a codebase given a find pattern.
It does not evaluate semantic properties of matches — that is the responsibility of the [filter](filter.md) step.
It does not modify code — that is the responsibility of the [modify](modify.md) step.

## Definition

Given a find pattern expressed in concrete syntax, the find step traverses the AST and returns all locations where the pattern matches syntactically.

### Pattern specification

The find pattern can be specified using one of three approaches:

* representation of the parser
* grammar of the language
* concrete syntax
* kind of node

**Decision**

We support concrete syntax.
As most developers are most familiar with concrete syntax, it minimises the learning curve and makes the tool easy to adopt.

We also support searching for particular kind of nodes.
We only support a limited set of language- and parser-agnostic kinds, such as `expression`, `statement`, `declaration`, and `class`.

### Find-next behaviour

The search for a next match can start after the first or last character of the current match.
For example, searching for `"aa"` within `"aaaa"` can yield either
two non-overlapping matches: `(0–1)` and `(2–3)`, or
three overlapping matches: `(0–1)`, `(1–2)`, and `(2–3)`.

For transformation, overlapping matches are problematic.
For example, it is ambiguous what the result of replacing `"aa"` with `"b"` within `"aaaa"` should be when the matches overlap.

**Decision**

Non-overlapping matches are used.
The search for the next match starts after the last character of the current match.

## Invariants / guarantees

* Matches are non-overlapping.
* Find patterns are expressed in concrete syntax.

## Related features

* [Matching](../../user/concepts/matching.md)

## Related tests

## Related code

## Notes

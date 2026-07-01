{ #architecture-rewrite-semantics }
# Rewrite semantics

**Stable ID:** `ARCHITECTURE-REWRITE-SEMANTICS`

## Purpose
Document design decisions that determine how the rewrite semantics are implemented.
For the domain model of changes and the rewrite step, see [Rewrite semantics](../../user/concepts/rewrite-semantics.md).

## General rules for combining changes

### Covered and overlapping replacements

Covered replacements are not applied to the source file.
Overlapping replacements are considered an error.
Yet, what about overlapping replacements that covered by another replacement? 

Two interpretations are possible:
1. **Application-first**:
Since covered replacements are not applied, overlaps among covered replacements are irrelevant and do not produce an error.
1. **Validation-first**:
Since overlapping replacements are inherently inconsistent, any overlap — regardless of whether replacements are covered — is considered an error.

**Decision**:

This framework adopts the **validation-first** interpretation.
Covered replacements are excluded from application, but included in validation.
Consequently, any overlap among replacements — whether covered or not — results in an error.

### Repeated changes

In the collected changes, the same changes might occur more than once.
To give some examples,
* a node is removed multiple times, and
* a node is prepended with the same text multiple times.

The behaviour of a change could be [idempotent](https://en.wikipedia.org/wiki/Idempotence) or not.
Furthermore, who makes this decision? The user or the framework?

### Impossible combinations

The combination of some changes is not possible.
For example, it is impossible to replace the same AST node with different texts.
The following behaviours are possible when such a situation occurs:
* **keep-first**: keep the first collected change and ignore later ones 
* **keep-last**: drop earlier collected changes and keep the last one
* **reject**: reject the combination and stop processing.

Diagnostics may be produced in addition to the selected behaviour
(e.g., warnings for keep-first/keep-last, errors for reject).

The reject behaviour is independent of the order in which changes are collected,
whereas keep-first and keep-last depend on that order.


### decision

Based on our experience with Renaissance that 
many features were never needed by high-quality transformations, 
we have decided to keep the rules as simple as possible.

1. The behaviour of changes is not configurable.
2. None of the changes is [idempotent](https://en.wikipedia.org/wiki/Idempotence).
3. Impossible changes are rejected.

As a consequence, we don't support corner cases but just throw an error, e.g., 
  * replacing the same node with text twice is an error even when the text is the same; and
  * removing two overlapping sequences of nodes is treated the same as replacing them and thus results in an error;

### Combinations at the same text location

Choices
1. Implementation freedom
1. Specify

We have chosen to specify as it makes the outcome more predictable and repeatable.

How to specify order?
Options include
1. (reversed) order of insertion,
1. (reversed) alphabetically, 
1. AST-based

We have chosen 
1. When different AST-nodes are involved to order based on AST structure, e.g., for prepends and appends of different AST nodes 
2. When the same AST-node is involved to order based on the (reversed) order of insertion into the collection of changes.
The direction depends on the operator - multiple prepends in the order and multiple appends in the reversed order of insertion.
# Rewrite semantics

{ #architecture-rewrite-semantics }

**Stable ID:** `ARCHITECTURE-REWRITE-SEMANTICS`

## Purpose

Document design decisions that determine how the rewrite semantics are implemented.
For the domain model of changes and the rewrite step, see [Rewrite semantics](../../user/concepts/rewrite-semantics.md).

## Impossible combinations of changes

The collected changes might contain changes whose combination is not possible.
For example, it is impossible to replace the same AST node with different texts.
The following behaviours are possible when such a situation occurs:

* **keep-first**: keep the first collected change and ignore later ones
* **keep-last**: drop earlier collected changes and keep the last one
* **reject**: reject the combination and stop processing.

Diagnostics may be produced in addition to the selected behaviour
(e.g., warnings for keep-first/keep-last, errors for reject).

The reject behaviour is independent of the order in which changes are collected,
whereas keep-first and keep-last depend on that order.

**Decision**:

For simplicity, we have decided that

1. Impossible changes are rejected.

Note that removing two overlapping sequences of nodes is treated the same as replacing them and thus considered an impossible change.

## Repeated changes

In the collected changes, the same changes might occur more than once.
To give some examples,

* a node is removed multiple times, and
* a node is prepended with the same text multiple times.

The behaviour of a change could be [idempotent](https://en.wikipedia.org/wiki/Idempotence) or not.
Furthermore, who makes this decision? The user or the framework?

**Decision**:
Based on our experience with Renaissance that
many features were never needed by high-quality transformations,
we have decided to keep the rules as simple as possible.

1. The behaviour of changes is not configurable by the user, but fixed by the framework.
1. None of the changes is [idempotent](https://en.wikipedia.org/wiki/Idempotence).

Note that non-idempotence results in quite different behaviours, depending on the kind of change:

* **Replacements**:
  replacing the same node twice is considered an impossible combination - even when the replacement is the same.

* **Insertions**:
  The same text can be appended multiple times to the same node.
  The text will be inserted as many times as the number of appends.

## Combinations at the same text location

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
1. When the same AST-node is involved to order based on the (reversed) order of insertion into the collection of changes.
The direction depends on the operator - multiple prepends in the order and multiple appends in the reversed order of insertion.

## TO BE Removed?

The following text is already covered by previous remarks, yet without some details. Are the details relevant, useful for our developers?

### Corner case: Identical replacements

Replacing the same AST node with different texts is not possible.
For the corner case of replacing the same AST node more than once with the same text,
different behaviours are possible:

1. error: the combination of replacements is considered invalid and an error is raised.
1. [idempotent](https://en.wikipedia.org/wiki/Idempotence):
   the combination of replacements is considered valid and the node is replaced by the text.
1. warning: the combination of replacements is considered suspicious, a warning is raised while the node is replaced by the text.

**Decision**:

This framework adopts the error behaviour for replacements.
In other words, replacing the same AST node more than once is considered an error, regardless of whether the replacement text is identical.
Note that as this framework considers removing an AST node equal to replacing that AST node with an empty string,
removing the same AST node more than once is considered an error.

### Corner case: Identical insertions

Prepending, appending, and surrounding different texts before, around, and after an AST node is possible.

For the corner case of using the same insertion operator on the same AST node with the same text more than once,
different behaviours are possible:

1. [idempotent](https://en.wikipedia.org/wiki/Idempotence): the text is inserted only once.
1. non-idempotent: the text is inserted more than once - as often as the insertion operator is used.

**Decision**:

This framework adopts non-idempotent insertion semantics:
applying append, prepend, or surround multiple times to the same AST node results in repeated insertions,
even when the inserted text is identical.

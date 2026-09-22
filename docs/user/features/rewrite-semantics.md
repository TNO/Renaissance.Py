# Rewrite semantics

{ #feature-rewrite-semantics }

**Stable ID:** `FEATURE-REWRITE-SEMANTICS`

## User-facing summary

The rewrite semantics feature governs how multiple collected changes — replacements and insertions —
are applied to a source file in a single rewrite step. It defines which combinations are valid and
which produce errors, so that transformation authors can reason about the outcome of composing changes.

## Related concepts

* [Rewrite semantics](../concepts/rewrite-semantics.md)

## Verified by test modules

* [Rewrite semantics test module](../../developer/modules/rewrite-semantics.md)
* BDD scenarios: `features/rewrite-semantics.feature`
* BDD steps: `features/steps/test-rewrite-semantics.py`

## Corner case: Dominated, overlapping replacements

When a replacement is dominated by another replacement, it is excluded from the
result — as if it were never collected. However, it is still checked for
overlaps with other changes. An overlap among dominated replacements therefore
still produces an error.

See [Architecture: rewrite semantics](../../developer/architecture/rewrite-semantics.md) for the rationale behind this choice.

## Scenario: Dominated changes

See [Figure 1.3 in the concept page](../concepts/rewrite-semantics.md#rewrite-semantics-dominated) for an illustration.

**Description**: Replacements hide dominated changes

| BDD keyword | step description                                                                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Given       | a programming language                                                                                                                               |
| and         | a source file written in that programming language                                                                                                   |
| and         | an AST extracted from that source file without errors                                                                                                |
| and         | a node of that AST                                                                                                                                   |
| and         | a sequence of descendant nodes of that node                                                                                                          |
| When        | that node is replaced by a text                                                                                                                      |
| and         | Rewrites, i.e., append, prepend, surround, and replace, are performed on that sequence of descendant nodes                                           |
| Then        | in the modified source file that node is replaced by the given text and all rewrites on that sequence of descendant nodes are not performed / hidden |

TODO: This description is only valid when a node is NOT considered a descendant of itself.
Check our definition (and implementation)!

## Scenario: Overlapping changes

See [Figure 1.2 in the concept page](../concepts/rewrite-semantics.md#rewrite-semantics-overlap) for an illustration.

**Description**: Replacements (including removal) cannot overlap

| BDD keyword | step description                                                       |
| ----------- | ---------------------------------------------------------------------- |
| Given       | a programming language                                                 |
| and         | a source file written in that programming language                     |
| and         | an AST extracted from that source file without errors                  |
| and         | two sequences of nodes of that AST that partly overlap                 |
| When        | both sequences are replaced with a string                              |
| Then        | an error with the text "overlapping changes are forbidden" is produced |

## Scenario: Combination of prepend and surround

1. on the same node: Prepend before surround
1. on a node and a descendant of that node:

   * Surround of node always before prepend of descendant of that node
   * Prepend of node always before surround of descendant of that node
1. on unrelated nodes: No interaction possible, so nothing to specify

## Scenario: Combination of append and surround

1. on the same node: Append after surround
1. on a node and a descendant of that node:

   * Surround of node always after append of descendant of that node
   * Append of node always after surround of descendant of that node
1. on unrelated nodes: No interaction possible, so nothing to specify

## Scenario: Combination of insertions and replacement on the same node

See
[prepend, surround, append, and replace](../concepts/rewrite-semantics.md#particular-combinations)
in the concept page for the formal rule: wherever the node's own text would appear in the
combined-insertions order, the replacement text appears instead when the node is also replaced.

1. prepend and replace: the prepend text always precedes the replacement text.
1. replace and append: the replacement text always precedes the append text.
1. surround and replace: the surround's before-text always precedes, and its after-text always
   follows, the replacement text.

Each of the three combinations holds regardless of collection order.

## Scenario: Combination of multiple prepends

1. on the same node: see
   [multiple prepends at the same text location](../concepts/rewrite-semantics.md#particular-combinations)
   in the concept page for the ordering rule and example.
1. on a node and a descendant of that node:
   See the concept page for an illustration of
   [prepends at the same text location](../concepts/rewrite-semantics.md#rewrite-semantics-prepends).

   | BDD keyword | step description                                                                                                                          |
   | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
   | Given       | a programming language                                                                                                                    |
   | and         | a source file written in that programming language                                                                                        |
   | and         | a string not contained in that source file                                                                                                |
   | and         | an AST extracted from that source file without errors                                                                                     |
   | and         | a node of that AST                                                                                                                        |
   | and         | a descendant of that node                                                                                                                 |
   | When        | that node is prepended by a concatenation of that string with "node"                                                                      |
   | and         | that descendant is prepended by a concatenation of that string with "descendant"                                                          |
   | Then        | in the modified source file the concatenation of that string with "node" occurs before the concatenation of that string with "descendant" |
1. on unrelated nodes: No interaction possible, so nothing to specify

## Scenario: Combination of multiple appends

1. on the same node: see
   [multiple appends at the same text location](../concepts/rewrite-semantics.md#particular-combinations)
   in the concept page for the ordering rule and example.
1. on a node and a descendant of that node

   | BDD keyword | step description                                                                                                                         |
   | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
   | Given       | a programming language                                                                                                                   |
   | and         | a source file written in that programming language                                                                                       |
   | and         | a string not contained in that source file                                                                                               |
   | and         | an AST extracted from that source file without errors                                                                                    |
   | and         | a node of that AST                                                                                                                       |
   | and         | a descendant of that node                                                                                                                |
   | When        | that node is append by a concatenation of that string with "node"                                                                        |
   | and         | that descendant is appended by a concatenation of that string with "descendant"                                                          |
   | Then        | in the modified source file the concatenation of that string with "node" occurs after the concatenation of that string with "descendant" |

1. on unrelated nodes: No interaction possible, so nothing to specify

## Scenario: Combination of multiple surrounds

Surround has before- and after-text.

1. on the same node: see
   [multiple surrounds at the same text location](../concepts/rewrite-semantics.md#particular-combinations)
   in the concept page.
1. on a node and a descendant of that node: see the concept page rule linked above for the general
   rule; the table below gives the testable scenario.

   | BDD keyword | step description                                                                              |
   | ----------- | --------------------------------------------------------------------------------------------- |
   | Given       | a programming language                                                                        |
   | and         | a source file written in that programming language                                            |
   | and         | an AST extracted from that source file without errors                                         |
   | and         | a node of that AST                                                                            |
   | and         | a descendant of that node                                                                     |
   | When        | that node is surrounded with a before-text and an after-text                                  |
   | and         | that descendant is surrounded with a before-text and an after-text                            |
   | Then        | in the modified source file the node's before-text occurs before the descendant's before-text |
   | and         | the descendant's after-text occurs before the node's after-text                               |
1. on unrelated nodes: No interaction possible, so nothing to specify

For example, given the addition `a + b` and two changes

1. the variable `a` should be wrapped in a call to `abs`, i.e., surrounded by `abs(` and `)`.
1. the addition should be wrapped in a call to `exp`, i.e., surrounded by `exp(` and `)`.

Note that

* both the variable `a` and the addition start at the same position in the source code.
* the node of the variable `a` is a descendant of the node of the addition.

The expected output is `exp(abs(a) + b)` and NOT `abs(exp(a) + b)`.

## Scenario: Combination of insertions at a shared sibling boundary

See the concept page for the general rule and an illustration of
   [insertions at a shared sibling boundary](../concepts/rewrite-semantics.md#rewrite-semantics-append-prepend):
   any text inserted at the end of a sibling (append text, or a surround's after-text) always precedes
   any text inserted at the start of the next, consecutive sibling (prepend text, or a surround's before-text),
   for all four combinations of the two operators — append/prepend, append/surround, surround/prepend,
   and surround/surround — and regardless of collection order.

| BDD keyword | step description                                                                                                                          |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Given       | a programming language                                                                                                                    |
| and         | a source file written in that programming language                                                                                        |
| and         | a string not contained in that source file                                                                                                |
| and         | an AST extracted from that source file without errors                                                                                     |
| and         | two consecutive nodes of that AST                                                                                                         |
| When        | the first node is appended (or surrounded, using its after-text) with a concatenation of that string with "node"                          |
| and         | the second node is prepended (or surrounded, using its before-text) with a concatenation of that string with "descendant"                 |
| Then        | in the modified source file the concatenation of that string with "node" occurs before the concatenation of that string with "descendant" |

## Example

Given the two statements in C++ `i++;++j;` and two changes

1. Append to each statement of a postfix increment operator, the comment `/* postfix increment */`
1. Prepend to each statement of a prefix increment operator, the comment `/* prefix increment */`

Note that the statement `i++;` ends and the statement `++j;` starts at the same position in the source code.

The expected output is `i++;/* postfix increment *//* prefix increment */++j;` and NOT `i++;/* prefix increment *//* postfix increment */++j;`.

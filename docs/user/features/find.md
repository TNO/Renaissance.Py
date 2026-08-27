# Find

{ #feature-find }

**Stable ID:** `FEATURE-FIND`

## MISC

1. Find all functionality
    1. Basic find - "code only" no nested structures
    1. find first, next, all - especially find "aa" in "aaaa" - two matches only
    1. basic nested find - "code only" nested if statements, nested for statements, ...
    1. single placeholder find
    1. multi placeholder find [sublist search] incl. error on illegal patterns (starting / ending with unconstrainted multi placeholder)
    1. multiple assignments find
    1. mixed

## Scenario: Find by kind

* Example, find if statements
* Nesting: A found match can contain another found match

## Scenario: kind of nodes

* Support language agnostics kinds
  * Definition, statement, expression, ...
* Support parser specific kinds
  * e.g. IASTIfStatement
* To be decided: support of kind patterns (like XPath)?

## Scenario: Find by AST Pattern matching

* Example, find `if ($x == MAX) { $$stmts; }`
* Nesting: A found match can contain another found match

## Scenario: Find All

AST Pattern are found consecutive, i.e., the found matches do not overlap

* Find "aa" in "aaa" has only one match
* Find "aa" in "aaaa" has only two non-overlapping matches

## Scenario: Find sequence

When searching for a sequence, we are not looking for sequences of exactly that length only,
we are looking for all (sub)sequences that match the sequence.

So the sequence of arguments `0,3` is found in `f(0,3)`, `g(0,3,1)`, `h(1,0,3)`, and even twice in `k(0,3,0,3)`.

## Scenario: Illegal find-patterns

As we are already looking for (sub)sequences, starting and/or ending a `find` pattern with
a `unconstrainted` multi placeholders is considered an error.

We allow for the following kinds of constraints

* Equivalence
  * For example, `$$args, $$args` to find argument lists in `f(0,3,0,3)`, `g(3,0,3,0,3)`, and `h()`.
* Back references
  * A back reference in a chained find uses the assigned value from an earlier find or match.

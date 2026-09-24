# Rewrite semantics

{ #concept-rewrite-semantics }

**Stable ID:** `CONCEPT-REWRITE-SEMANTICS`

## Purpose

Define deterministic semantics of collecting and committing changes.

## Scope

This concept covers the collection and combination of change operations.
These change operations can have two views on the code:
code can be viewed as a sequence of characters or as an abstract syntax tree.
This concept describes both the commonalities between the views and
the combination of the changes within the different views.

## Change process

The change process consists of the following steps:

1. Given the view, interpret the code,
1. collect changes in that view, and
1. commit changes to produce the final text.

## Unit of view

The two views have different units:
The unit of character-based changes is a character.
The unit of AST-based changes is an AST node.

A change operator acts on zero or more consecutive units.
In particular, a character-based operator acts on consecutive characters and
an AST-based change operator acts on consecutive AST nodes, i.e., adjacent sibling nodes.

All consecutive units correspond to a range of text in the original code.
For zero consecutive units this text range is empty, but it has a well-defined location.
For instance, the empty parameter list of a function definition denotes zero AST nodes,
located between the brackets.

## Kinds of changes

We distinguish two kinds of changes: replacements and insertions.

Each replacement substitutes zero or more consecutive units with some text.
A removal is `just` a replacement with an empty string.

Each insertion add text related to zero or more consecutive units.
Three kinds of insertions are supported, i.e., prepend, append, and surround,
that insert text at the start, end, and both locations of the consecutive units.

## Particular combinations

We have the following rules to combine and commit the collected changes.

1. Replacements affecting the same AST node(s) are erroneous.  
Whenever different changes are applied to the same range of text, an error will be raised.
For AST-based pattern matching, this situation can only occur when replacements are applied
to the same node or to the same sequence of nodes.
So when multiple replacements are affecting the same AST node(s) an error is raised.  
Figure 1.1 shows an example where different replacements are applied to the same AST node.  
/// html | figure#rewrite-semantics-equal  
![Multiple replacements to the same AST-node](rewrite-semantics-images/rewrite-semantics-equal.png)
*Figure 1.1 (CONCEPT-REWRITE-SEMANTICS-EQUAL): Example of multiple replacements to the same AST node.*
///

1. Overlapping replacements are erroneous.  
Whenever different changes are applied to overlapping ranges of text, an error will be raised.
For AST-based pattern matching, this situation can only occur when replacements are applied to
overlapping sequence of nodes.
So when multiple replacements are affecting the same sequence of AST nodes an error is raised.  
Figure 1.2 shows an example where replacements are applied to overlapping sequences of arguments
to a function call in which case an error is raised.  
/// html | figure#rewrite-semantics-overlap
![Overlapping replacements](rewrite-semantics-images/rewrite-semantics-overlap.png)
*Figure 1.2 (CONCEPT-REWRITE-SEMANTICS-OVERLAP): Example of overlapping replacements.*
///

1. Dominated changes are ignored.  
A change is dominated if its range is a proper subset of the range of another change.
For AST-based pattern matching this may occur when a change associated with an AST node lies
within the range of a change associated with one of its ancestors.  
/// html | figure#rewrite-semantics-dominated
![Change dominated by another change](rewrite-semantics-images/rewrite-semantics-dominated.png)
*Figure 1.3 (CONCEPT-REWRITE-SEMANTICS-DOMINATED): Example of a dominated change.*
///

1. Multiple prepends at the same text location  
   * different nodes:
     Prepend of ancestor before prepend of descendant.  
/// html | figure#rewrite-semantics-prepends
![Prepends at the same textual location](rewrite-semantics-images/rewrite-semantics-prepends.png)
*Figure 1.4 (CONCEPT-REWRITE-SEMANTICS-PREPENDS): Example of prepends of different AST nodes at the same textual location.*
///
   * same node:
     In order of insertion of change / in collection order.  
     Example: Prepend N - ... - Prepend 2 - Prepend 1 - AST Node text

1. Multiple appends at the same text location
   * different nodes:
     Append of ancestor after append of descendant.  
/// html | figure#rewrite-semantics-appends
![Appends at the same textual location](rewrite-semantics-images/rewrite-semantics-appends.png)
*Figure 1.5 (CONCEPT-REWRITE-SEMANTICS-APPENDS): Example of appends of different AST nodes at the same textual location.*
///
   * same node:
     In reverse order of insertion of change / in reversed collection order.  
     Example: AST Node text - Append 1 - Append 2 - ... - Append N

1. Multiple surrounds at the same text location  
   * a node and one of its ancestors (the only way two different AST nodes can share the same
     start and/or end location, since the descendant's range is always nested within the
     ancestor's range):
     the before-text of the ancestor's surround always precedes the before-text of the
     descendant's surround, and the after-text of the descendant's surround always precedes
     the after-text of the ancestor's surround — like nested brackets, where the outer bracket
     opens first and closes last.
   * same node:
     Before-text in order of insertion of change / in collection order;
     after-text in reverse order of insertion of change / in reversed collection order.  
     Example: Surround Before N - ... - Surround Before 2 - Surround Before 1 - AST Node text -
     Surround After 1 - Surround After 2 - ... - Surround After N

The direction depends on the operator: multiple prepends (and surround before-texts) follow the
order of insertion into the collection of changes, while multiple appends (and surround
after-texts) follow the reversed order of insertion.

1. Insertions at a shared sibling boundary  
Can only happen for consecutive sibling nodes: any text inserted at the end location of a sibling
(append text, or the after-text of a surround) always precedes any text inserted at the start location
of the next, consecutive sibling (prepend text, or the before-text of a surround).
Figure 1.6 illustrates the append/prepend case; the same ordering applies when either or both
operators are a surround instead.  
/// html | figure#rewrite-semantics-append-prepend
![Append and prepend at the same textual location](rewrite-semantics-images/rewrite-semantics-append-prepend.png)
*Figure 1.6 (CONCEPT-REWRITE-SEMANTICS-APPEND-PREPEND):
Example of append and prepend of adjacent siblings at the same textual location.*
///

1. Prepend, surround, append, and replace
   * same node  
     The expected order in the modified source file is:  
     prepend_text, surround_before_text, (AST Node text | replacement text), surround_after_text, append_text  
     where `(AST Node text | replacement text)` means exactly one of the two is present: the
     node's own text when it is not replaced, or the replacement text when a
     [replacement](../../glossary.md#replacement) is also applied to that node — never both.  
     When there are multiple prepends, surrounds, and/or appends on the same node, each group
     of insertions follows its own ordering rule given above, and the groups combine in the
     same relative positions, e.g., for N prepends, M surrounds, and P appends:  
     Prepend N - ... - Prepend 1 - Surround Before M - ... - Surround Before 1 - (AST Node text | replacement text) -
     Surround After 1 - ... - Surround After M - Append 1 - ... - Append P

## Summary

Summary of the rewrite-semantics

* Dominance rule: dominated operations are ignored
* Consistency rule: overlapping operations are not possible
* Containment rules:
  * A replace operation on an AST node, hides all operations on all contained AST nodes (a.k.a. descendants),
  i.e., they are ignored - prepend, append and around operations on that AST node are NOT affected.
  * A prepend to an AST node is always before a prepend to any contained AST node
  * An append to an AST node is always after an append to any contained AST node
  * The before-text of a surround of an AST node is always before the before-text of a surround to any contained AST node
  * The after-text of a surround of an AST node is always after the after-text of a surround to any contained AST node
* Sequence rule - Given two consecutive AST Nodes (a.k.a. siblings):
  * Any text inserted at the end of the first AST Node (append text, or a surround's after-text) is
  always before any text inserted at the start of the second AST Node (prepend text, or a surround's before-text)

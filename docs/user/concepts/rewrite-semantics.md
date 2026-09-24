# Rewrite semantics

{ #concept-rewrite-semantics }

**Stable ID:** `CONCEPT-REWRITE-SEMANTICS`

## Purpose

Define deterministic semantics of collecting and committing changes.

## Scope

This concept covers the collection and combination of change operations.
These change operations can have two views on the code:
code can be viewed as a sequence of characters or as an abstract syntax tree.
This concept describes both the commonalities and differences between the views,
and the combination of the changes from these two views.

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

All consecutive units correspond to a text range in the original code.
For zero consecutive units the text range is empty,
yet the location in the original code is specified.
For instance, an empty parameter list of a function definition denotes zero AST nodes,
located between the brackets.

## Kinds of changes

We distinguish two kinds of changes: replacements and insertions.

Each replacement substitutes zero or more consecutive units with some text.
A removal is `just` a replacement with an empty string.

Each insertion adds text related to zero or more consecutive units.
Three kinds of insertions are supported, i.e., prepend, append, and surround,
that insert text at the start, end, and both locations of the consecutive units.

## Particular combinations

We have the following rules to combine and commit the collected changes.

1. Replacements affecting the same text range are erroneous.  
For both views it holds that whenever different replacements are applied to the same consecutive units,
an error will be raised.
Figure 1.1 shows an example where different replacements are applied to the same AST node, and an error is raised.  
/// html | figure#rewrite-semantics-equal  
![Multiple replacements to the same AST-node](rewrite-semantics-images/rewrite-semantics-equal.png)
*Figure 1.1 (CONCEPT-REWRITE-SEMANTICS-EQUAL): Example of multiple replacements to the same AST node.*
///

1. Replacements affecting partly overlapping text ranges are erroneous.  
For both views it holds that whenever different replacements are applied to partly overlapping consecutive units, an error will be raised.
Figure 1.2 shows an example where replacements are applied to partly overlapping consecutive AST nodes,
some arguments of a function call, and an error is raised.  
/// html | figure#rewrite-semantics-overlap
![Overlapping replacements](rewrite-semantics-images/rewrite-semantics-overlap.png)
*Figure 1.2 (CONCEPT-REWRITE-SEMANTICS-OVERLAP): Example of overlapping replacements.*
///

1. Surrounds affecting partly overlapping text ranges are erroneous.  
For both views it holds that whenever different surrounds are applied to overlapping consecutive units, an error will be raised.

1. Dominated changes are ignored.  
A change is dominated if its text range is a proper subset of the text range of another change, i.e., its text range is contained by another text range.
Figure 1.3 shows an example where the replacement of an AST node dominates the replacement of one of its descendants.  
/// html | figure#rewrite-semantics-dominated
![Change dominated by another change](rewrite-semantics-images/rewrite-semantics-dominated.png)
*Figure 1.3 (CONCEPT-REWRITE-SEMANTICS-DOMINATED): Example of a dominated change.*
///

1. Multiple prepends at the same text location  
   * different consecutive units:  
     The insertion that prepends the longer text range is before
     the insertion that prepends the shorter text range.
     For the AST-based view holds that a
     prepend of ancestor is before a prepend of descendant.
     Figure 1.4 shows an example where the prepend of an AST node is before the prepend of one of its descendants.  
/// html | figure#rewrite-semantics-prepends
![Prepends at the same textual location](rewrite-semantics-images/rewrite-semantics-prepends.png)
*Figure 1.4 (CONCEPT-REWRITE-SEMANTICS-PREPENDS): Example of prepends of different AST nodes at the same textual location.*
///
   * same consecutive units:  
     In order of insertion of change / in collection order.  
     Example: Prepend N - ... - Prepend 2 - Prepend 1 - text of consecutive units.

1. Multiple appends at the same text location
   * different consecutive units:  
     The insertion that appends the longer text range is after
     the insertion that appends the shorter text range.
     For the AST-based view holds that an
     append of ancestor is after an append of descendant.
     Figure 1.5 shows an example where the append of an AST node is after the append of one of its descendants.  
/// html | figure#rewrite-semantics-appends
![Appends at the same textual location](rewrite-semantics-images/rewrite-semantics-appends.png)
*Figure 1.5 (CONCEPT-REWRITE-SEMANTICS-APPENDS): Example of appends of different AST nodes at the same textual location.*
///
   * same consecutive units:  
     In reverse order of insertion of change / in reversed collection order.  
     Example: text of consecutive units - Append 1 - Append 2 - ... - Append N.

1. Multiple surrounds at the same text location  
   * adjacent, non-overlapping consecutive units (before + after):  
     The after-insertion of the surround that ends at the text location is before
     the before-insertion of the surround that starts at the text location.
   * different, overlapping consecutive units (before + before or after + after):  
     The before-insertion of the surround with the longer text range is before
     the before-insertion of the surround with the shorter text range, and
     the after-insertion of the surround with the longer text range is after
     the after-insertion of the surround with the shorter text range
     — like nested brackets, where the outer bracket opens first and closes last.
     In the AST-based view, this situation can only occur with
     a node and one of its ancestors,
     as being in a containment relation is the only way two different AST nodes
     can share the same start and/or end location.
   * same consecutive units (before + before and after + after):  
     Before-text in order of insertion of change / in collection order;
     after-text in reverse order of insertion of change / in reversed collection order.  
     Example: Surround Before N - ... - Surround Before 2 - Surround Before 1 -
     text of consecutive units -
     Surround After 1 - Surround After 2 - ... - Surround After N.

1. Different insertions at the same location  
   In the AST-based view, this situation can only occur for consecutive sibling nodes:
   any text inserted at the end location of a sibling (append text, or the after-text of a surround) always
   precedes any text inserted at the start location of the next, consecutive sibling
   (prepend text, or the before-text of a surround).  
   Figure 1.6 illustrates the append/prepend case; the same ordering applies when either or both
operators are a surround instead.  
/// html | figure#rewrite-semantics-append-prepend
![Append and prepend at the same textual location](rewrite-semantics-images/rewrite-semantics-append-prepend.png)
*Figure 1.6 (CONCEPT-REWRITE-SEMANTICS-APPEND-PREPEND):
Example of append and prepend of adjacent siblings at the same textual location.*
///

1. Prepend, surround, append, and replace
   * same consecutive units:  
     The expected order in the modified source file is:  
     prepend_text, surround_before_text, (text of consecutive units | replacement text), surround_after_text, append_text  
     where `(text of consecutive units | replacement text)` means exactly one of the two is present: the
     text of the consecutive units when they are not replaced, or the replacement text when a
     [replacement](../../glossary.md#replacement) is also applied to those consecutive units — never both.  
     When there are multiple prepends, surrounds, and/or appends on the same node, each group
     of insertions follows its own ordering rule as described above, and the groups combine in the
     same relative positions, e.g., for N prepends, M surrounds, and P appends:  
     Prepend N - ... - Prepend 1 -
     Surround Before M - ... - Surround Before 1 -
     (text of consecutive units | replacement text) -
     Surround After 1 - ... - Surround After M -
     Append 1 - ... - Append P

## Summary

Summary of the rewrite-semantics

* Dominance rule: dominated operations are ignored
* Consistency rule: overlapping operations are not possible
* Containment rules:
  * A replace operation on an AST node, hides all operations on all contained AST nodes (a.k.a. descendants),
  i.e., they are ignored - prepend, append and surround operations on that AST node are NOT affected.
  * A prepend to an AST node is always before a prepend to any contained AST node
  * An append to an AST node is always after an append to any contained AST node
  * The before-text of a surround of an AST node is always before the before-text of a surround to any contained AST node
  * The after-text of a surround of an AST node is always after the after-text of a surround to any contained AST node
* Sequence rule - Given two consecutive AST Nodes (a.k.a. siblings):
  * Any text inserted at the end of the first AST Node (append text, or a surround's after-text) is
  always before any text inserted at the start of the second AST Node (prepend text, or a surround's before-text)
* Multiple applications rule - The direction depends on the operator:
  multiple prepends (and surround before-texts) follow the order of collection of the changes,
  while multiple appends (and surround after-texts) follow the reversed order of collection.

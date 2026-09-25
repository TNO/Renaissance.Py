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

These steps are performed for each view;
see [Combination of the two views](#combination-of-the-two-views) for the combination of the changes of both views.

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
That location depends on the interpretation of the code,
i.e., on the parser for the AST-based view and on the regular expression matcher for the character-based view.
As zero consecutive units contain no units at all, their location distinguishes them:
zero consecutive units at different locations in the code are different,
e.g., the empty parameter lists of two different function definitions.

## Kinds of changes

We distinguish two kinds of changes: replacements and insertions.

Each replacement substitutes zero or more consecutive units with some text.
A removal is `just` a replacement with an empty string.

Each insertion adds text related to zero or more consecutive units.
Three kinds of insertions are supported, i.e., prepend, append, and surround,
that insert text at the start, end, and both locations of the consecutive units.

## Particular combinations

We have the following rules to combine and commit the collected changes.
Each rule compares the consecutive units that the changes act on,
using the following relations between consecutive units:

* Consecutive units are the *same* when they consist of exactly the same units,
  and, for zero consecutive units, when their locations are the same.
* Consecutive units *partly overlap* when they share at least one unit,
  while each of them also has a unit that the other does not have.
* Consecutive units *contain* other consecutive units when the two are not the same and
  every unit of the latter is a unit of the former or lies within one of them.
  In the character-based view a character never lies within another character,
  so the containing characters are always longer than the contained characters.
  In the AST-based view a unit lies within another unit when it is a descendant of that unit,
  so the containing nodes are not always longer than the contained nodes.

Each relation implies a relation between the corresponding text ranges, but the units are decisive:
the same units have equal text ranges, partly overlapping units have partly overlapping text ranges,
and containing units have a text range that includes the contained text range.
Note that the including text range is not always longer:
in the AST-based view the text range of a node and the text range of one of its descendants can be equal,
e.g., in the CDT parser for C/C++ a declaration statement node and the declaration node it contains have the same text range.

Two changes can also be unrelated, i.e., their consecutive units are disjoint and their text ranges do not overlap.
Such changes do not affect each other, so no rule is needed to combine them.

1. Replacements affecting the same consecutive units are erroneous.  
In both views, an error is raised whenever multiple replacements are applied to the same consecutive units.
These replacements also have equal, and therefore overlapping text ranges.
Figure 1.1 shows an example where multiple replacements are applied to the same AST node, and an error is raised.  
/// html | figure#rewrite-semantics-equal  
![Multiple replacements to the same AST-node](rewrite-semantics-images/rewrite-semantics-equal.png)
*Figure 1.1 (CONCEPT-REWRITE-SEMANTICS-EQUAL): Example of multiple replacements to the same AST node.*
///

1. Replacements affecting partly overlapping consecutive units are erroneous.  
In both views, an error is raised whenever different replacements are applied to partly overlapping consecutive units.
These replacements also have partly overlapping text ranges.
In the AST-based view this can only occur for consecutive siblings of the same parent node.
Figure 1.2 shows an example where replacements are applied to partly overlapping consecutive AST nodes,
some arguments of a function call, and an error is raised.  
/// html | figure#rewrite-semantics-overlap
![Overlapping replacements](rewrite-semantics-images/rewrite-semantics-overlap.png)
*Figure 1.2 (CONCEPT-REWRITE-SEMANTICS-OVERLAP): Example of overlapping replacements.*
///

1. Surrounds affecting partly overlapping consecutive units are erroneous.  
In both views, an error is raised whenever different surrounds are applied to partly overlapping consecutive units.
These surrounds also have partly overlapping text ranges.

1. Changes are ignored when a replacement affects containing consecutive units.  
In both views, a change is ignored when the consecutive units of a replacement contain the consecutive units of that change.
The text range of the ignored change is then contained in the text range of that replacement.
In the AST-based view this includes the case where the text range of a node and the text range of one of its
descendants are equal, as the units and not the text ranges are decisive.
Changes affecting the same consecutive units as the replacement are not ignored;
the last rule below describes how they are combined.
Figure 1.3 shows an example where the replacement of an AST node dominates the replacement of one of its descendants.  
/// html | figure#rewrite-semantics-dominated
![Change dominated by another change](rewrite-semantics-images/rewrite-semantics-dominated.png)
*Figure 1.3 (CONCEPT-REWRITE-SEMANTICS-DOMINATED): Example of a dominated change.*
///

1. Multiple prepends at the same text location  
   * different consecutive units:  
     Different consecutive units can only share their start location when one of them contains the other.
     The prepend of the containing consecutive units is before
     the prepend of the contained consecutive units.
     In the AST-based view, a prepend of an ancestor is before a prepend of a descendant.
     Figure 1.4 shows an example where the prepend of an AST node is before the prepend of one of its descendants.  
/// html | figure#rewrite-semantics-prepends
![Prepends at the same textual location](rewrite-semantics-images/rewrite-semantics-prepends.png)
*Figure 1.4 (CONCEPT-REWRITE-SEMANTICS-PREPENDS): Example of prepends of different AST nodes at the same textual location.*
///
   * same consecutive units:  
     In the order in which the changes were collected.  
     Example: Prepend N - ... - Prepend 2 - Prepend 1 - text of consecutive units.

1. Multiple appends at the same text location
   * different consecutive units:  
     Different consecutive units can only share their end location when one of them contains the other.
     The append of the containing consecutive units is after
     the append of the contained consecutive units.
     In the AST-based view, an append of an ancestor is after an append of a descendant.
     Figure 1.5 shows an example where the append of an AST node is after the append of one of its descendants.  
/// html | figure#rewrite-semantics-appends
![Appends at the same textual location](rewrite-semantics-images/rewrite-semantics-appends.png)
*Figure 1.5 (CONCEPT-REWRITE-SEMANTICS-APPENDS): Example of appends of different AST nodes at the same textual location.*
///
   * same consecutive units:  
     In the reverse order in which the changes were collected.  
     Example: text of consecutive units - Append 1 - Append 2 - ... - Append N.

1. Multiple surrounds at the same text location  
   * different consecutive units, where one contains the other
     (before + before or after + after):  
     The before-text of the surround of the containing consecutive units is before
     the before-text of the surround of the contained consecutive units, and
     the after-text of the surround of the containing consecutive units is after
     the after-text of the surround of the contained consecutive units
     — like nested brackets, where the outer bracket opens first and closes last.
     In the AST-based view, this situation can only occur with
     a node and one of its ancestors,
     as being in a containment relation is the only way two different AST nodes
     can share the same start and/or end location.
   * same consecutive units (before + before and after + after):  
     Before-text in the order in which the changes were collected;
     after-text in the reverse order in which the changes were collected.  
     Example: Surround Before N - ... - Surround Before 2 - Surround Before 1 -
     text of consecutive units -
     Surround After 1 - Surround After 2 - ... - Surround After N.

1. Different insertions at the same location  
   In both views, this situation can only occur for adjacent consecutive units:
   any text inserted at the end location of the preceding consecutive units
   (append text, or the after-text of a surround) always precedes any text inserted at the start
   location of the following consecutive units (prepend text, or the before-text of a surround).
   In the AST-based view these units are adjacent sibling nodes.  
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
     When there are multiple prepends, surrounds, and/or appends on the same consecutive units, each group
     of insertions follows its own ordering rule as described above, and the groups combine in the
     same relative positions, e.g., for N prepends, M surrounds, and P appends:  
     Prepend N - ... - Prepend 1 -
     Surround Before M - ... - Surround Before 1 -
     (text of consecutive units | replacement text) -
     Surround After 1 - ... - Surround After M -
     Append 1 - ... - Append P

## Combination of the two views

The [change process](#change-process) is performed for each view.
Changes from both views are combined in the following order:

1. All changes are collected, in the character-based view as well as in the AST-based view,
1. the changes in the AST-based view are combined using the rules above,
   which produces character-based changes, and
1. all character-based changes, both the collected and the produced ones,
   are combined using the same rules.

The changes of the AST-based view are thus reduced to character-based changes before the final combination,
so the rules are always applied to changes of a single view.

## Summary

Summary of the rewrite-semantics

* Consistency rule: replacements on the same or on partly overlapping consecutive units are erroneous,
  and so are surrounds on partly overlapping consecutive units
* Dominance rule: changes are ignored when a replacement affects containing consecutive units
* Containment rules - given consecutive units that contain other consecutive units:
  * A replacement of the containing units hides all changes to the contained units,
  i.e., they are ignored - prepend, append and surround operations on the containing units are NOT affected.
  * A prepend of the containing units is always before a prepend of the contained units
  * An append of the containing units is always after an append of the contained units
  * The before-text of a surround of the containing units is always before the before-text of a surround of the contained units
  * The after-text of a surround of the containing units is always after the after-text of a surround of the contained units
* Sequence rule - given two adjacent consecutive units, e.g., adjacent sibling AST nodes:
  * Any text inserted at the end of the preceding units (append text, or a surround's after-text) is
  always before any text inserted at the start of the following units (prepend text, or a surround's before-text)
* Multiple applications rule - the direction depends on the operator:
  multiple prepends (and surround before-texts) follow the order of collection of the changes,
  while multiple appends (and surround after-texts) follow the reversed order of collection.

{ #concept-rewrite-semantics }
# Rewrite semantics

**Stable ID:** `CONCEPT-REWRITE-SEMANTICS`

## Purpose
Define predictable and understandable semantics for collected and committed changes.

## Kind of changes

We distinguish two kinds of changes: Replacements and insertions.

Each replacement affects a range within the original text. 
In AST-based pattern matching that range of text corresponds to either an AST node or a sequence of consecutive sibling nodes.
A removal is `just` a replacement with an empty string. 

Each insertion relates to a location in the original text.
In AST-based pattern matching that location of text corresponds to either the start location or the end location of an AST node.
Three kind of insertions are supported, i.e., prepend, append, and around, that insert text at the start, end, and both locations of the AST node.

## Rewrite step
1. parse code,
2. collect changes,
3. commit changes.

## General rules for combining changes

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

## Particular combinations

We have the following rules to combine and commit the collected changes.

1. Replacements affecting the same AST node(s) are erroneous.

As different changes cannot be applied to the same range of text,
an error will be raised whenever such situation occurs.
For AST-based pattern matching, this situation can only occur when replacements are applied to the same node or to the same sequence of nodes.
So when multiple replacements are affecting the same AST node(s) an error is raised.

Figure 1.1 shows an example where different replacements are applied to the same AST node.

<a name="rewrite-semantics-equal">

![Multiple replacements to the same AST-node](rewrite-semantics/rewrite-semantics-equal.png)

*Figure 1.1 (CONCEPT-REWRITE-SEMANTICS-EQUAL): Example of multiple replacements to the same AST node.*

</a>

2. Overlapping replacements are erroneous.

As different changes cannot be applied to overlapping ranges of text,
an error will be raised whenever such situation occurs.
For AST-based pattern matching, this situation can only occur when replacements are applied to overlapping sequence of nodes.
So when multiple replacements are affecting the same seqeunce of AST nodes an error is raised.

Figure 1.2 shows an example where replacements are applied to overlapping sequences of arguments to a function call in which case an error is raised.

<a name="rewrite-semantics-overlap">

![Overlapping replacements](rewrite-semantics/rewrite-semantics-overlap.png)

*Figure 1.2 (CONCEPT-REWRITE-SEMANTICS-OVERLAP): Example of overlapping replacements.*

</a>

3. Covered changes are ignored.

subset relation


A change is covered if its range is a subset of the range of another change.
For AST-based pattern matching this may occur when a change associated with an AST node lies within the range of a change associated with one of its ancestors. 

<a name="rewrite-semantics-cover">

![Change covered by another change](rewrite-semantics/rewrite-semantics-cover.png)

*Figure 1.3 (CONCEPT-REWRITE-SEMANTICS-COVER): Example of overlapping sequences of AST nodes.*

</a>

4. Multiple prepends at the same text location
    * different nodes
    * same node

5. Multiple appends at the same text location
    * different nodes
    * same node

6. Appends and prepends at the same text location


7. Prepend, surround, and append

The expected order in the modified source file is:

prepend_text, surround_before_text, AST Node text, surround_after_text, append_text

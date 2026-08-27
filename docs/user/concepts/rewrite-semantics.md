# Rewrite semantics

{ #concept-rewrite-semantics }

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
Three kind of insertions are supported, i.e., prepend, append, and around,
that insert text at the start, end, and both locations of the AST node.

## Rewrite step

Each rewrite step consists of the following, sequential steps:

1. parse code,
1. collect changes, and
1. commit changes.

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

    * different nodes

        Prepend of ancestor before prepend of descendant.

        /// html | figure#rewrite-semantics-prepends

        ![Prepends at the same textual location](rewrite-semantics-images/rewrite-semantics-prepends.png)

        *Figure 1.4 (CONCEPT-REWRITE-SEMANTICS-PREPENDS): Example of prepends of different AST nodes at the same textual location.*

        ///

      * same node
          In order of insertion of change / in collection order

1. Multiple appends at the same text location
   
      * different nodes

        Append of ancestor after append of descendant.

        /// html | figure#rewrite-semantics-appends

        ![Appends at the same textual location](rewrite-semantics-images/rewrite-semantics-appends.png)

        *Figure 1.5 (CONCEPT-REWRITE-SEMANTICS-APPENDS): Example of appends of different AST nodes at the same textual location.*

        ///

       * same node

           In reverse order of insertion of change / in reversed collection order

1. Appends and prepends at the same text location
        Can only happen for consecutive sibling nodes
        append of sibling before prepend of next, consecutive sibling

    /// html | figure#rewrite-semantics-append-prepend

    ![Append and prepend at the same textual location](rewrite-semantics-images/rewrite-semantics-append-prepend.png)

    *Figure 1.6 (CONCEPT-REWRITE-SEMANTICS-APPEND-PREPEND):
    Example of append and prepend of adjacent siblings at the same textual location.*

    ///

1. Prepend, surround, and append
    * same node
       The expected order in the modified source file is:

       prepend_text, surround_before_text, AST Node text, surround_after_text, append_text

## MISC

* Rewrite-semantics
  * Dominance rule: dominated operations are ignored
  * Consistency rule: overlapping operations are not possible
  * Containment rules:
    * A replace operation on an AST node, hides all operations on all contained AST nodes (a.k.a. descendants),
      i.e., they are ignored - prepend, append and around operations on that AST node are NOT affected.
    * A prepend to an AST node is always before a prepend to any contained AST node
    * An append to an AST node is always after an append to any contained AST node
  * Sequence rule - Given two consecutive AST Nodes (a.k.a. siblings):
    * An append to the first AST Node is always before a prepend to the second AST Node

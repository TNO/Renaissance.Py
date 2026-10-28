<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Composition

{ #concept-composition }

**Stable ID:** `CONCEPT-COMPOSITION`

## Purpose

Composition combines language-specific patterns with language-agnostic orchestration.

## Composing changes

Changes can be composed in two ways:

* **within one rewrite step**: changes are collected against the same code and committed together;
* **across consecutive rewrite steps**: each step works on the code produced by the previous step.

The two ways differ in what a change can see:
within one rewrite step every change refers to the original code,
whereas across consecutive rewrite steps a later change can refer to the result of an earlier change.

### Within one rewrite step

A [rewrite step](../../glossary.md#rewrite-step) interprets the code once, collects changes, and commits them together;
see [Rewrite semantics](rewrite-semantics.md#change-process).
Combining changes in one step has the following benefits:

1. **Positions stay valid.**
    Every change refers to the original code.
    Applying a change immediately would shift the positions of all later changes.
1. **No interpretation between changes.**
    The code is parsed once.
    The intermediate text after only some of the changes need not be parsable,
    e.g., after replacing an opening bracket but before replacing its closing bracket.
1. **One read and one write per file.**
1. **All or nothing.**
    The commit either applies all changes or, when the changes are erroneous, none of them.
1. **Conflicts are detected.**
    Erroneous combinations, such as overlapping replacements, can only be detected when all changes are known.
1. **Deterministic and predictable result.**
    The [rules of rewrite semantics](rewrite-semantics.md#particular-combinations) define how the collected changes combine.
    Most rules do not depend on the collection order:
    erroneous combinations are rejected and nested insertions are ordered by containment, regardless of that order.
    Only multiple insertions on the same consecutive units depend on the collection order,
    and the rules define their order in the result.
1. **Independent contributions.**
    Different analyses can contribute changes without knowing about each other.
1. **One review.**
    The result is a single difference per file, which can be previewed before it is written.

The trade-off is that changes cannot see each other's effects:
every analysis finds and filters on the original code, not on the code that results from other changes.

### Across consecutive rewrite steps

Consecutive rewrite steps are needed when a later change depends on the result of an earlier change,
e.g., when a pattern only matches code that an earlier change produces.
Each rewrite step interprets the code produced by the previous step.
This has the following consequences:

* **Intermediate text must be parsable.**
    The text produced by each step, except the last, is the input of the next step,
    so it must be parsable by the parser of that next step.
    The final text doesn't have to be parsable.
    Different parsers can be used in the different steps, as is for example the case in transpilation.
* **Earlier positions are invalid.**
    Positions and AST nodes of an earlier step do not refer to the code of a later step;
    changes are only combined for nodes of the same parse,
    see [Position consistency](../../developer/architecture/position-consistency.md).
* **The order of the steps matters.**
    A later step sees, and can change, the result of an earlier step.
    No conflicts are detected between steps: a later replacement can silently replace text inserted by an earlier step.
* **Each step costs** a parse, a read, and a write per file.

### Choosing between the two

Prefer one rewrite step when every change can be determined from the original code.
Use consecutive rewrite steps only when a change cannot be determined from the original code.

Choosing the smallest units to change often keeps changes in one rewrite step.
For example, renaming `f` to `g` in `f(f(x))` by replacing each call with `g` and its original arguments
makes the replacement of the inner call a [dominated change](../../glossary.md#dominated-change):
it is ignored, and the result is `g(f(x))`.
Replacing only the function names of both calls changes disjoint units and gives `g(g(x))` in one step.

The same distinction exists for Python regular expressions:
`re.sub` finds all matches in the original text and replaces them in one step,
whereas calling `re.sub` repeatedly corresponds to consecutive steps;
see [Regular expressions in Python](../../developer/architecture/environment/regular-expressions.md).

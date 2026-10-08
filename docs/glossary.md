# Glossary

{ #glossary }

**Stable ID:** `GLOSSARY`

This glossary collects short definitions for domain-specific terms used across the documentation.
Each entry links to the concept page that is the authoritative source of the definition.

---

## A

### Analysis

Extracts data from and computes information about a [code base](#code-base).
See [Analysis](user/concepts/analysis.md).

### Ancestor

An AST node that contains another node within its subtree, at any depth,
including the node itself.
A *proper ancestor* excludes the node itself; the direct parent is the nearest
proper ancestor.

### Append

An [insertion](#insertion) that adds text immediately after the end location of an AST node.
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

### Around

See [Surround](#surround).

### AST (Abstract Syntax Tree)

A hierarchical representation of source code produced by a compiler front-end,
abstracting over syntactic details such as whitespace, comments, and delimiters.
See [Matching](user/concepts/matching.md).

### Automation

Code-oriented processing that operates on the structure of source code rather than on raw text, and therefore requires parser integration.
See [Automation](user/concepts/automation.md).

---

## C

### Change

A collected modification to the original source text, either a [replacement](#replacement) or an [insertion](#insertion).
Changes are collected during the *collect* step of a [rewrite step](#rewrite-step) and applied during the *commit* step.
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

### Code base

The full set of production, validation, and
supporting artifacts — including source code, tests, build scripts, and documentation —
that together constitute a software system.
A code base is typically multi-language, multi-project, and evolves over decades.
See [Evolving and maintaining code](user/concepts/code-base-evolution-and-maintenance.md).

### Collection of changes

The act of registering one or more [changes](#change) against a syntax tree during
the *collect* step of a [rewrite step](#rewrite-step), before any changes are
committed. The sequence in which changes are registered is the *collection order*,
which affects output ordering only when the same operator is applied multiple times
to the same node.
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

### Composition

Combining language-specific patterns with language-agnostic orchestration to form higher-level analysis or transformation strategies.
See [Composition](user/concepts/composition.md).

### CST (Concrete Syntax Tree)

A full parse tree that retains every syntactic token, including whitespace and comments.
See [Matching](user/concepts/matching.md).

---

## D

### Descendant

An AST node contained within the subtree of another node, at any depth,
including the node itself.
A *proper descendant* excludes the node itself; the direct children are the nearest
proper descendants.

### Dominated change

A [change](#change) whose range is a proper subset of the range of another change,
and which is therefore silently ignored during the [rewrite step](#rewrite-step).
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

---

## F

### Filter

A check applied to candidate [matches](#match) that produces an *include*, *remove*, or *undecisive* result,
thereby refining the match set before further processing.
See [Filter](user/concepts/filter.md).

---

## I

### Insertion

A [change](#change) that adds text at a location in the original source without removing any existing text.
The supported insertion kinds are [prepend](#prepend), [append](#append), and [surround](#surround).
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

### Integration

A parser-specific bridge (e.g., tree-sitter, Clang, Python's `ast` module) that makes a parser's native
nodes conform to the core [AST](#ast-abstract-syntax-tree) node's `Protocol`, implemented as a wrapper, an
adapter, or via duck typing.
See [ADR 14](developer/architecture/adr/14_code_repositories.md).

---

## M

### Match

An occurrence found in the source that satisfies the criteria of a pattern under a particular [conceptual view](#matching).
See [Matching](user/concepts/matching.md).

### Matching

The process of locating occurrences in source code that satisfy a pattern,
governed by a conceptual view that defines granularity, structure, classification, and equality.
See [Matching](user/concepts/matching.md).

---

## N

### Node (AST node)

A single element in an [AST](#ast-abstract-syntax-tree), representing a syntactic
construct such as a statement, expression, identifier, or punctuation token.
Every node has a [range](#range) in the original source text, defined by its
start and end position.
See [Matching](user/concepts/matching.md).

---

## O

### Observability

The degree to which the behavior of the tool can be inspected and described,
supporting understanding and debugging of analysis and transformation results.
See [Observability](user/concepts/observability.md).

---

## P

### Prepend

An [insertion](#insertion) that adds text immediately before the start location of an AST node.
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

---

## R

### Range

A contiguous region of the original source text, expressed as a start and end offset.
Every AST [node](#node-ast-node) has a range; the range of a [replacement](#replacement)
is derived from the range of the replaced node or sequence of nodes.
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

### Recipe

A combination of multiple standard analyses and transformations (rules) applied in a coordinated way to
perform a non-trivial refactoring; more powerful than a single find / filter / modify rule.
See [ADR 14](developer/architecture/adr/14_code_repositories.md).

### Rejuvenation

A concrete, runnable application of [Renaissance](#renaissance) that evolves a [code base](#code-base) in
response to change, so that it keeps delivering value. That change originates from one of three sources:

- the **customer** — e.g., additional or changed requirements;
- the **organization** — e.g., business strategy, process, or structure (see the BAPO model: Business,
  Architecture, Process, Organisation); or
- the **environment** — e.g., the language, dependency, library, OS, or tooling versions a code base
  relies on.

Transpilation (translating from one programming language to another) and migration (moving to a new
language, dependency, or tooling version) are approaches used to respond to such change.
See [ADR 14](developer/architecture/adr/14_code_repositories.md).

### Removal

A [replacement](#replacement) where the replacement text is the empty string, effectively deleting the text of a source [range](#range).
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

### Renaissance

The parser-agnostic core of the project: the unified AST model, match-pattern engine, rewriter, and other
language- and parser-agnostic components.
See [ADR 14](developer/architecture/adr/14_code_repositories.md).

### Replacement

A [change](#change) that substitutes the text of a source [range](#range) with new text.
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

### Rewrite step

The sequential process of (1) parsing source code, (2) collecting [changes](#change), and
(3) committing those changes to produce modified source code.
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

---

## S

### Sibling

Two AST nodes are siblings when they share the same direct parent.
*Adjacent siblings* are consecutive children of the same parent node in the AST.

### Standard analyses and transformations

A library of reusable, pre-built analysis and transformation building blocks that can be combined to improve quality and reduce duplication.
See [Standard analyses and transformations](user/concepts/standard-libraries.md).

### Surround

An [insertion](#insertion) that adds text at both the start and end locations of an AST node simultaneously.
The resulting order in the modified source is: `surround_before_text`, AST node text, `surround_after_text`.
See [Rewrite semantics](user/concepts/rewrite-semantics.md).

---

## T

### Token

Smallest meaningful unit of code.

### Transformation

Manipulating code using find / filter / manipulate workflows to produce modified source.
See [Transformation](user/concepts/transformation.md).

### Trivia

White spaces and comments.

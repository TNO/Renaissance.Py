<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# tree-sitter binding

{ #concept-parser-bindings-tree-sitter }

**Stable ID:** `CONCEPT-PARSER-BINDINGS-TREE-SITTER`

## Purpose

Describe the binding that parses code with tree-sitter into lossless syntax tree (LST) nodes, which the core matches and
rewrites.

## Scope

Every language for which a tree-sitter grammar is installed; the tests use the grammars of Python, Java and C++.

## Definition

- `TreeSitterAdapter` parses code with the tree-sitter grammar it is given, and converts the parse tree into an `LST`.
- `LST` holds the root `LSTNode` of a tree.
- `LSTNode` is a node: its parser kind is the tree-sitter node type, and its semantic kind follows from that type.
- `TreeSitterPatternFactory` creates patterns, with placeholders such as `$x`, from text.
- `LstVisualizer` renders an `LST` as a Mermaid graph.

## Invariants / guarantees

- A tree-sitter node type without a semantic kind gets `SemanticKind.NODE`; its `kind_key` is then the node type.
- Two nodes are equal when their kind keys, their relevant properties and their children are equal; comments are ignored.

## Extension points

Another language is supported by passing its tree-sitter grammar module to `TreeSitterAdapter`.

## Non-goals

Resolving names, includes or macros; tree-sitter only parses the text it is given.

## Related features

None.

## Related tests

`test/unit/parser_bindings/tree_sitter/`

## Related code

`src/renaissance/parser_bindings/tree_sitter/`

## API

::: renaissance.parser_bindings.tree_sitter
    options:
      heading_level: 3

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Python ast binding

{ #concept-parser-bindings-python-ast }

**Stable ID:** `CONCEPT-PARSER-BINDINGS-PYTHON-AST`

## Purpose

Describe the binding that parses Python code with the `ast` module of the standard library into nodes, which the core matches
and rewrites.

## Scope

Python source code that the `ast` module of the running Python version parses.

## Definition

- `PythonRstTranslationUnit` parses a file or text with `ast`, and records the references between its nodes.
- `PythonRstNode` is a node: its parser kind is the `ast` class name, and its semantic kind follows from that name.
- `PythonRSTReference` is a reference from one node to another, such as a call of a function or the use of a type.
- `ASTExtension` lets the `ast` nodes themselves be used as nodes, without a wrapper.
- `convert_function` rewrites the signature of a function to take a leading `self` parameter.

`PythonFactory` and `PythonPatternFactory`, which create nodes and patterns with placeholders such as `$x`, are in
`renaissance.parser_bindings.python.ast.factory`. They serve the `ast`, libcst and tree-sitter nodes at once, until each binding
has its own.

## Invariants / guarantees

- An `ast` class without a semantic kind gets `SemanticKind.NODE`; its `kind_key` is then the class name.
- Every statement class of `ast` has a semantic kind.

## Extension points

None.

## Non-goals

Preserving the layout and the comments of the code; the `ast` module drops them. The libcst binding keeps them.

## Related features

None.

## Related tests

`test/unit/parser_bindings/python/ast/`

## Related code

`src/renaissance/parser_bindings/python/ast/`

## API

::: renaissance.parser_bindings.python.ast
    options:
      heading_level: 3

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Python libcst binding

{ #concept-parser-bindings-python-libcst }

**Stable ID:** `CONCEPT-PARSER-BINDINGS-PYTHON-LIBCST`

## Purpose

Describe the binding that parses Python code with libcst into nodes of its concrete syntax tree, which the core matches and
rewrites.

## Scope

Python source code that libcst parses.

## Definition

- `PythonCstTranslationUnit` parses a file or text with libcst, and resolves the positions of its nodes and, with the scope
  analysis of libcst, the uses and definitions of names.
- `PythonCstNode` is a node: its parser kind is the libcst class name, and its semantic kind follows from that name.

Nodes and patterns are created with `PythonFactory` and `PythonPatternFactory` of the Python ast binding, which serve the
libcst nodes too, until each binding has its own.

## Invariants / guarantees

- The offsets of a node are byte offsets in the encoded source text, the unit in which the rewriter splices.
- `references` and `referenced_by` follow the scope analysis of libcst.

## Extension points

None.

## Non-goals

Resolving names across files.

## Related features

- [Type parameter modernization](../../../features/type_parameter_modernization.md)

## Related tests

`test/unit/parser_bindings/python/libcst/`

## Related code

`src/renaissance/parser_bindings/python/libcst/`

## API

::: renaissance.parser_bindings.python.libcst
    options:
      heading_level: 3

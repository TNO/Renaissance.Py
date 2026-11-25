<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.python.ast.rst_node

{ #codemod-parser-bindings-python-ast-rst-node }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-PYTHON-AST-RST-NODE`

## Responsibility

Wraps the nodes of the standard library `ast` module as nodes of the core, and records the references between them.

## Location

`src/renaissance/parser_bindings/python/ast/rst_node.py`

## Public entry points

`renaissance.parser_bindings.python.ast` exports:

- `PythonRstNode`, with `load(file_path)` and `load_from_text(text, file_name)`, and the node protocol: parser and semantic
  kind, properties, children, signature, offsets, siblings, `references` and `referenced_by`;
- `PythonRstTranslationUnit`, the parsed file, which builds the references between its nodes on first use;
- `PythonRSTReference`, a reference from one node to another.

## Internal structure

The semantic kind and the operator of a node are looked up in `kinds`; `util.convert` turns a line and column into an offset.
`ImplicitNode` stands in where the source has no node.

## Validated by test modules

- `test/unit/parser_bindings/python/ast/test_rst_node___parsing.py`
- `test/unit/parser_bindings/python/ast/test_rst_node___pythonic.py`
- `test/unit/parser_bindings/python/ast/test_rst_node___references.py`
- `test/unit/parser_bindings/python/ast/test_rst_node___shower.py`

## Related concepts

- [Python ast binding](../../../../user/parser_bindings/python/ast/ast.md)

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.python.libcst.cst_node

{ #codemod-parser-bindings-python-libcst-cst-node }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-PYTHON-LIBCST-CST-NODE`

## Responsibility

Wraps the nodes of the concrete syntax tree of libcst as nodes of the core.

## Location

`src/renaissance/parser_bindings/python/libcst/cst_node.py`

## Public entry points

`renaissance.parser_bindings.python.libcst` exports:

- `PythonCstNode`, with `load(file_path)` and `load_from_text(text, file_name)`, and the node protocol: parser and semantic
  kind, children, signature, offsets, siblings, `references` and `referenced_by`;
- `PythonCstTranslationUnit`, the parsed file, with the positions of its nodes and the uses and definitions of names.

## Internal structure

The translation unit wraps the module in a libcst `MetadataWrapper`, for the positions and the scopes of its nodes, and
converts line and column positions into byte offsets. The semantic kind is looked up in `PYTHON_KIND_MAP` of the Python ast
binding; this import is a known violation, resolved when each binding has its own map.

## Validated by test modules

- `test/unit/parser_bindings/python/libcst/test_cst_node___parsing.py`
- `test/unit/parser_bindings/python/libcst/test_cst_node___references.py`

## Related concepts

- [Python libcst binding](../../../../user/parser_bindings/python/libcst/libcst.md)

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.tree_sitter.lst

{ #codemod-parser-bindings-tree-sitter-lst }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-TREE-SITTER-LST`

## Responsibility

Defines the LST node, which implements the node protocol of the core, and the LST that holds its root.

## Location

`src/renaissance/parser_bindings/tree_sitter/lst.py`

## Public entry points

`renaissance.parser_bindings.tree_sitter` exports `LSTNode` and `LST`.

## Internal structure

`LSTNode` derives its semantic kind from its parser kind with `TREE_SITTER_KIND_MAP`, and implements `__eq__` with
`equal_in_properties` and `equal_in_children` of the shared helpers, ignoring `IRRELEVANT_PROPS` and comment nodes. Its
siblings come from the navigation of the core, and its `repr` from `format_node`.

The clang adapter builds `LSTNode`s too; see Known violations in [repository structure](../../architecture/repository_structure.md).

## Validated by test modules

- `test/unit/parser_bindings/tree_sitter/test_lst___node_protocol_metadata.py`
- `test/unit/parser_bindings/tree_sitter/test_lst___python.py`

## Related concepts

- [tree-sitter binding](../../../user/parser_bindings/tree_sitter/tree_sitter.md)

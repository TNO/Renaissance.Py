<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.tree_sitter.factory

{ #codemod-parser-bindings-tree-sitter-factory }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-TREE-SITTER-FACTORY`

## Responsibility

Creates patterns from text with a tree-sitter adapter.

## Location

`src/renaissance/parser_bindings/tree_sitter/factory.py`

## Public entry points

`renaissance.parser_bindings.tree_sitter` exports `TreeSitterPatternFactory(adapter, language)`, with `create(text)`, which
returns the root node, and `create_statements`, `create_statement` and `create_expression`, which return the top-level
statements, the last statement, and the last child of the last statement.

## Internal structure

`create` parses with a `TreeSitterAdapter`; another adapter, such as the clang adapter, is asked for its LST directly.

## Validated by test modules

- `test/unit/parser_bindings/tree_sitter/test_factory.py`

## Related concepts

- [tree-sitter binding](../../../user/parser_bindings/tree_sitter/tree_sitter.md)

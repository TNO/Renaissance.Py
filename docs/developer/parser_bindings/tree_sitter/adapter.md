<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.tree_sitter.adapter

{ #codemod-parser-bindings-tree-sitter-adapter }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-TREE-SITTER-ADAPTER`

## Responsibility

Parses code with a tree-sitter grammar and converts the parse tree into an LST.

## Location

`src/renaissance/parser_bindings/tree_sitter/adapter.py`

## Public entry points

`renaissance.parser_bindings.tree_sitter` exports `TreeSitterAdapter(grammar_module)`, with `parse_code(source_code)`, which
returns the tree-sitter parse tree, and `to_lst(source_code, tree)`, which converts it into an `LST`.

## Internal structure

`to_lst` replaces the `$` of placeholders with `replace_dollar` of the core, and converts each tree-sitter node recursively
into an `LSTNode`. A node whose text is a placeholder gets the kind that `detect_placeholder` of the core coerces it to, and
keeps its tree-sitter type in the property `original_node_type`.

## Validated by test modules

- `test/unit/parser_bindings/tree_sitter/test_adapter___languages.py`
- `test/unit/parser_bindings/tree_sitter/test_adapter___matchers.py`
- `test/unit/parser_bindings/tree_sitter/test_adapter___structural_matcher.py`
- `test/unit/parser_bindings/tree_sitter/test_adapter___tree_sitter_parse.py`

## Related concepts

- [tree-sitter binding](../../../user/parser_bindings/tree_sitter/tree_sitter.md)

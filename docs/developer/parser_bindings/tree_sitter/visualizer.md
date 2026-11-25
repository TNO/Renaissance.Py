<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.tree_sitter.visualizer

{ #codemod-parser-bindings-tree-sitter-visualizer }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-TREE-SITTER-VISUALIZER`

## Responsibility

Renders an LST as a Mermaid graph.

## Location

`src/renaissance/parser_bindings/tree_sitter/visualizer.py`

## Public entry points

`renaissance.parser_bindings.tree_sitter` exports `LstVisualizer`, with `render(lst)`, which returns the Mermaid text.

## Internal structure

Each node becomes a Mermaid node labelled with its semantic kind, parser kind, offset and a short id derived from its signature
by `signature_to_id`, and each child an edge from its parent.

## Validated by test modules

- `test/unit/parser_bindings/tree_sitter/test_visualizer.py`

## Related concepts

- [tree-sitter binding](../../../user/parser_bindings/tree_sitter/tree_sitter.md)

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.tree_sitter.kinds

{ #codemod-parser-bindings-tree-sitter-kinds }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-TREE-SITTER-KINDS`

## Responsibility

Maps tree-sitter node types onto the semantic kinds of the core.

## Location

`src/renaissance/parser_bindings/tree_sitter/kinds.py`

## Public entry points

None; `TREE_SITTER_KIND_MAP` is internal to the binding.

## Internal structure

One dictionary, with the node types of the grammars of Python, Java and C++.

## Validated by test modules

None of its own; `test/unit/parser_bindings/tree_sitter/test_lst___node_protocol_metadata.py` checks the semantic kinds of
LST nodes.

## Related concepts

- [tree-sitter binding](../../../user/parser_bindings/tree_sitter/tree_sitter.md)

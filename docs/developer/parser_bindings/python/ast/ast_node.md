<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.python.ast.ast_node

{ #codemod-parser-bindings-python-ast-ast-node }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-PYTHON-AST-AST-NODE`

## Responsibility

Lets the nodes of the standard library `ast` module be used as nodes of the core, without a wrapper.

## Location

`src/renaissance/parser_bindings/python/ast/ast_node.py`

## Public entry points

`renaissance.parser_bindings.python.ast` exports `ASTExtension`, whose static methods `PythonFactory(ast.AST)` patches onto
`ast.AST`: `load_from_ast`, and the parser kind, semantic kind, properties, children and signature of a node.

## Internal structure

The semantic kind is looked up in `PYTHON_KIND_MAP` of `kinds`.

## Validated by test modules

None of its own; `test/unit/parser_bindings/python/ast/test_factory___protocol_metadata.py` and
`test/unit/parser_bindings/python/ast/test_factory___node_kinds.py` check the native `ast` nodes that the factory creates.

## Related concepts

- [Python ast binding](../../../../user/parser_bindings/python/ast/ast.md)

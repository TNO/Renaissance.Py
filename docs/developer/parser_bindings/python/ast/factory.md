<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.python.ast.factory

{ #codemod-parser-bindings-python-ast-factory }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-PYTHON-AST-FACTORY`

## Responsibility

Creates Python nodes, and patterns with placeholders such as `$x` and `$$x`, from files and text, for the `ast`, libcst and
tree-sitter nodes.

## Location

`src/renaissance/parser_bindings/python/ast/factory.py`

## Public entry points

The module itself, outside the `__all__` of `renaissance.parser_bindings.python.ast`:

- `PythonFactory(clazz)`, for `PythonRstNode`, `PythonCstNode`, `LSTNode` or `ast.AST`, with `create(file_path)` and
  `create_from_text(text, file_name)`;
- `PythonPatternFactory(factory)`, with `create`, `create_statements`, `create_statement`, `create_expression`,
  `create_decorators` and `create_kwargs`;
- `PythonPattern`, the pattern node these return.

## Internal structure

`PythonPattern` wraps a node and derives its pattern kind from a placeholder name. For `ast.AST`, `PythonFactory` patches the
methods of `ASTExtension` onto the class; for `LSTNode`, it parses with tree-sitter.

The factory imports the libcst and tree-sitter bindings; these imports are known violations, resolved when each binding has its
own factory. Exporting it from the package would make `python.ast` and `python.libcst` import each other.

## Validated by test modules

- `test/unit/parser_bindings/python/ast/test_factory___ast_matcher_basic.py`
- `test/unit/parser_bindings/python/ast/test_factory___ast_matcher_representation.py`
- `test/unit/parser_bindings/python/ast/test_factory___keywords.py`
- `test/unit/parser_bindings/python/ast/test_factory___matcher.py`
- `test/unit/parser_bindings/python/ast/test_factory___matcher_basic.py`
- `test/unit/parser_bindings/python/ast/test_factory___node_kinds.py`
- `test/unit/parser_bindings/python/ast/test_factory___offset_encoding.py`
- `test/unit/parser_bindings/python/ast/test_factory___patternic_style.py`
- `test/unit/parser_bindings/python/ast/test_factory___patterns.py`
- `test/unit/parser_bindings/python/ast/test_factory___protocol_metadata.py`
- `test/unit/parser_bindings/python/ast/test_factory___type_parameters.py`

## Related concepts

- [Python ast binding](../../../../user/parser_bindings/python/ast/ast.md)
- [Python libcst binding](../../../../user/parser_bindings/python/libcst/libcst.md)
- [tree-sitter binding](../../../../user/parser_bindings/tree_sitter/tree_sitter.md)

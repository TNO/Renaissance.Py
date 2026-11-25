<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.python.ast.kinds

{ #codemod-parser-bindings-python-ast-kinds }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-PYTHON-AST-KINDS`

## Responsibility

Maps the class names of Python nodes onto the semantic kinds of the core, and the `ast` operator classes onto their symbols.

## Location

`src/renaissance/parser_bindings/python/ast/kinds.py`

## Public entry points

None; `PYTHON_KIND_MAP` and `PYTHON_OPERATOR_MAP` are internal to the binding.

## Internal structure

Two dictionaries. The libcst binding uses `PYTHON_KIND_MAP` too; this import is a known violation, resolved when each binding
has its own map.

## Validated by test modules

None of its own; `test/unit/parser_bindings/python/ast/test_factory___protocol_metadata.py` checks that every statement class
of `ast` has a semantic kind.

## Related concepts

- [Python ast binding](../../../../user/parser_bindings/python/ast/ast.md)

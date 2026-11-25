<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.python.ast.util

{ #codemod-parser-bindings-python-ast-util }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-PYTHON-AST-UTIL`

## Responsibility

Converts a source position into an offset, and the signature of a function into one with a leading `self` parameter.

## Location

`src/renaissance/parser_bindings/python/ast/util.py`

## Public entry points

`renaissance.parser_bindings.python.ast` exports `convert_function(fun)`, which the `unit_to_pytest` recipe uses.
`convert(lines, line_nr, col)` is internal to the binding.

## Internal structure

Two functions.

## Validated by test modules

None of its own; `test/unit/parser_bindings/python/ast/test_factory___offset_encoding.py` checks the offsets of the nodes, and
`test/recipes/test_unit_to_pytest.py` the recipe that uses `convert_function`.

## Related concepts

- [Python ast binding](../../../../user/parser_bindings/python/ast/ast.md)

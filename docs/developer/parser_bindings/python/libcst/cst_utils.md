<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.python.libcst.cst_utils

{ #codemod-parser-bindings-python-libcst-cst-utils }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-PYTHON-LIBCST-CST-UTILS`

## Responsibility

Helpers over the libcst tree of one module: its top-level statements, the names they read or bind and the comment trailing a
line.

## Location

`src/renaissance/parser_bindings/python/libcst/cst_utils.py`

## Public entry points

None; `module_statements`, `trailing_of_sole_statement`, `names_read_by` and `assigned_names` are internal to the binding.

## Internal structure

`names_read_by` walks an expression with a libcst visitor that skips the names of attributes and keyword arguments.

## Validated by test modules

- `test/unit/parser_bindings/python/libcst/test_cst_utils.py`

## Related concepts

- [Python libcst binding](../../../../user/parser_bindings/python/libcst/libcst.md)

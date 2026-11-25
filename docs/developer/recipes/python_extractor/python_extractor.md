<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# recipes.python_extractor.python_extractor

{ #codemod-recipes-python-extractor-python-extractor }

**Stable ID:** `CODEMOD-RECIPES-PYTHON-EXTRACTOR-PYTHON-EXTRACTOR`

## Responsibility

Builds a codebase graph of Python modules, with their imports, functions and classes, from the Python standard library `ast`
parser.

## Location

`src/renaissance/recipes/python_extractor/python_extractor.py`

## Public entry points

`renaissance.recipes.python_extractor` exports `PythonExtractor()`: `process(file)` parses a file and adds its module,
imports, functions and classes to `graph`, and its tree to `codebase`; `save_graph(filename)` writes `graph` as GraphML.

## Internal structure

The `graph` and `codebase` of `PythonExtractor` are class attributes, so all instances share them.

The module is parser specific: it walks the nodes of the `python.ast` binding, a declared dependency.

## Validated by test modules

- `test/unit/recipes/python_extractor/test_python_extractor.py`

## Related concepts

- [Python extractor](../../../user/recipes/python_extractor/python_extractor.md)

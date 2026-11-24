<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Recipe Python extractor

{ #codemod-recipes-python-extractor }

**Stable ID:** `CODEMOD-RECIPES-PYTHON-EXTRACTOR`

## Responsibility

Builds a codebase graph of Python modules, with their imports, functions and classes, from the Python standard library `ast`
parser.

## Location

`src/renaissance/recipes/python_extractor/`

## Public entry points

The `__all__` of `renaissance.recipes.python_extractor`; see the [API reference](../../api/recipes/python_extractor.md).

- `PythonExtractor()`: `process(file)` parses a file and adds its module, imports, functions and classes to `graph`, and its
  tree to `codebase`; `save_graph(filename)` writes `graph` as GraphML.

## Internal structure

- `python_extractor.py` defines `PythonExtractor`. Its `graph` and `codebase` are class attributes, so all instances share them.

`recipes.python_extractor` imports `core.model`. It is parser specific: it walks the nodes of the `python.ast` binding, a
declared dependency.

## Related features

- [Analysis workflows](../../../user/features/analysis_workflows.md)

## Related concepts

- [Python extractor](../../../user/recipes/python_extractor.md)

## Validated by test modules

`test/unit/recipes/python_extractor/`

## Extension points

None.

## Non-goals

Resolving the references between modules.

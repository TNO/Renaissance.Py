<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Python extractor

{ #concept-recipes-python-extractor }

**Stable ID:** `CONCEPT-RECIPES-PYTHON-EXTRACTOR`

## Purpose

Describe the graph that the Python extractor builds of a Python codebase.

## Scope

Python files, parsed with the Python standard library `ast` parser.

## Definition

- `PythonExtractor.process` adds a file to the graph: an edge `contains` from its folder to its module, an edge `include` from
  the module to each import, and an edge `definition` from the module to each function and class.
- `PythonExtractor.save_graph` writes the graph as GraphML.

## Invariants / guarantees

- The extractor reads the code; it does not change it.

## Extension points

None.

## Non-goals

Resolving the references between modules.

## Related features

- [Analysis workflows](../../features/analysis_workflows.md)

## Related tests

`test/unit/recipes/python_extractor/`

## Related code

`src/renaissance/recipes/python_extractor/`

## API

::: renaissance.recipes.python_extractor
    options:
      heading_level: 3

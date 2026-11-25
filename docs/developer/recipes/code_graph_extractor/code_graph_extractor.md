<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# recipes.code_graph_extractor.code_graph_extractor

{ #codemod-recipes-code-graph-extractor-code-graph-extractor }

**Stable ID:** `CODEMOD-RECIPES-CODE-GRAPH-EXTRACTOR-CODE-GRAPH-EXTRACTOR`

## Responsibility

Builds code graphs of Python, Java and C++ files, with their folders, functions and calls, from the tree-sitter parser.

## Location

`src/renaissance/recipes/code_graph_extractor/code_graph_extractor.py`

## Public entry points

`renaissance.recipes.code_graph_extractor` exports:

- `BaseCodeGraphExtractor(language, lib_path)`: `extract(files)` parses each file with the tree-sitter grammar `lib_path` and
  adds it to `graph`; `save_graph(filename)` writes `graph` as GraphML to `out_graphml/`.
- `PythonCodeGraphExtractor`, `JavaCodeGraphExtractor` and `CppCodeGraphExtractor` add the functions or methods and the calls
  of one language.

## Internal structure

Importing the module creates the directory `out_graphml/`.

The module is parser specific: it parses with the `tree_sitter` binding, a declared dependency.

## Validated by test modules

- `test/unit/recipes/code_graph_extractor/test_code_graph_extractor.py`

## Related concepts

- [Code graph extractor](../../../user/recipes/code_graph_extractor/code_graph_extractor.md)

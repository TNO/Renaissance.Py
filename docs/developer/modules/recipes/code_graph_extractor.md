<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Recipe code graph extractor

{ #codemod-recipes-code-graph-extractor }

**Stable ID:** `CODEMOD-RECIPES-CODE-GRAPH-EXTRACTOR`

## Responsibility

Builds code graphs of Python, Java and C++ files, with their folders, functions and calls, from the tree-sitter parser.

## Location

`src/renaissance/recipes/code_graph_extractor/`

## Public entry points

The `__all__` of `renaissance.recipes.code_graph_extractor`; see the
[API reference](../../api/recipes/code_graph_extractor.md).

- `BaseCodeGraphExtractor(language, lib_path)`: `extract(files)` parses each file with the tree-sitter grammar `lib_path` and
  adds it to `graph`; `save_graph(filename)` writes `graph` as GraphML to `out_graphml/`.
- `PythonCodeGraphExtractor`, `JavaCodeGraphExtractor` and `CppCodeGraphExtractor` add the functions or methods and the calls
  of one language.

## Internal structure

- `code_graph_extractor.py` defines the extractors. Importing it creates the directory `out_graphml/`.

`recipes.code_graph_extractor` imports `core.model`. It is parser specific: it parses with the `tree_sitter` binding, a
declared dependency.

## Related features

- [Analysis workflows](../../../user/features/analysis_workflows.md)

## Related concepts

- [Code graph extractor](../../../user/recipes/code_graph_extractor.md)

## Validated by test modules

`test/unit/recipes/code_graph_extractor/`

## Extension points

A subclass of `BaseCodeGraphExtractor` implements `_process_file` for another language.

## Non-goals

Resolving a call to the function it calls.

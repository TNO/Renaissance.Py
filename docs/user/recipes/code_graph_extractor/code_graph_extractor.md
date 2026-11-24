<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Code graph extractor

{ #concept-recipes-code-graph-extractor }

**Stable ID:** `CONCEPT-RECIPES-CODE-GRAPH-EXTRACTOR`

## Purpose

Describe the graph that the code graph extractors build of a Python, Java or C++ codebase.

## Scope

Files parsed with a tree-sitter grammar.

## Definition

- `extract` adds each file to the graph: an edge `contains` from its folder to the file, an edge `defines` from the file to
  each function or method, and an edge `calls` from the file to each call target.
- `PythonCodeGraphExtractor`, `JavaCodeGraphExtractor` and `CppCodeGraphExtractor` differ in how they name a function and a
  call target.
- `save_graph` writes the graph as GraphML to `out_graphml/`.

## Invariants / guarantees

- The extractors read the code; they do not change it.
- A file that cannot be read or parsed is reported and skipped.

## Extension points

A subclass of `BaseCodeGraphExtractor` implements `_process_file` for another language.

## Non-goals

Resolving a call to the function it calls.

## Related features

- [Analysis workflows](../../features/analysis_workflows.md)

## Related tests

`test/unit/recipes/code_graph_extractor/`

## Related code

`src/renaissance/recipes/code_graph_extractor/`

## API

::: renaissance.recipes.code_graph_extractor
    options:
      heading_level: 3

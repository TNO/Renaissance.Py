<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# parser_bindings.project.project_scanner

{ #codemod-parser-bindings-project-project-scanner }

**Stable ID:** `CODEMOD-PARSER-BINDINGS-PROJECT-PROJECT-SCANNER`

## Responsibility

Finds the source files of a project from its build artefacts or its directory tree.

## Location

`src/renaissance/parser_bindings/project/project_scanner.py`

## Public entry points

`renaissance.parser_bindings.project` exports `ProjectScanner`, `CppScanner`, `BearCppScanner`, `JavaScanner` and
`PythonScanner`. Each has `find_sources()`, which returns the sorted paths of the source files; `BearCppScanner` also has
`run_bear()`.

## Internal structure

`CppScanner` reads `compile_commands.json`, and `BearCppScanner` extends it by running `bear -- make` when that file is missing.
`JavaScanner` and `PythonScanner` walk a directory tree; `PythonScanner` prunes the directories it skips, so it does not descend
into them.

The module imports nothing from Renaissance.Py.

## Validated by test modules

- `test/unit/parser_bindings/project/test_project_scanner.py`

## Related concepts

- [Project scanners](../../../user/parser_bindings/project/project.md)

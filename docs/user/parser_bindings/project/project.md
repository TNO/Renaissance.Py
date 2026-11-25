<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Project scanners

{ #concept-parser-bindings-project }

**Stable ID:** `CONCEPT-PARSER-BINDINGS-PROJECT`

## Purpose

Describe the scanners that find the source files of a project, which a recipe then processes.

## Scope

Build artefacts and source trees: a `compile_commands.json`, a `Makefile` run through Bear, and a directory tree of Java or
Python files.

## Definition

- `ProjectScanner` is the base class; `find_sources()` returns the paths of the source files.
- `CppScanner` returns the files listed in a `compile_commands.json`, sorted and without duplicates.
- `BearCppScanner` first generates the `compile_commands.json` with Bear when it is missing.
- `JavaScanner` returns the `.java` files under a directory.
- `PythonScanner` returns the `.py` files under a directory, or under some of its subdirectories, skipping hidden files and
  directories, `__pycache__` and `venv`.

## Invariants / guarantees

- The scanners return paths, sorted; they do not parse the files.

## Extension points

A scanner for another kind of project subclasses `ProjectScanner` and implements `find_sources()`.

## Non-goals

Parsing the files that a scanner finds, which is the task of the other parser bindings.

## Related features

None.

## Related tests

`test/unit/parser_bindings/project/`

## Related code

`src/renaissance/parser_bindings/project/`

## API

::: renaissance.parser_bindings.project
    options:
      heading_level: 3

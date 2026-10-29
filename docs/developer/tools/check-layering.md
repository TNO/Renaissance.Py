<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Layering check

[Import Linter](https://import-linter.readthedocs.io/) fails the build when a module imports another module that it is not
allowed to depend on. It checks the sources and the unit tests.

## Where the rules live

The rules are the contracts in `[tool.importlinter]` of `pyproject.toml`. That section is their single source of truth:
[Repository structure](../architecture/repository-structure.md) explains why the rules exist, but does not repeat them.

| Contract                               | Rule                                                                                   |
| -------------------------------------- | -------------------------------------------------------------------------------------- |
| `layers`                               | recipes above parser bindings above the core; within the core, the order of its parts  |
| `bindings-use-model-pattern-matching`  | a parser binding does not import `core.rewriting` or `core.processing`                 |
| `recipes-without-bindings`             | a recipe does not import a parser binding, unless the exemption is backed by evidence  |
| `clang-independent` and the like       | a parser binding imports no other parser binding, one contract per binding             |

Each contract lists modules of today's packages, because the target packages do not exist yet. Moving a module during the
migration is an edit to these lists. Once a target package exists, its line in a contract shrinks to that one package.

## Tests follow the same rules

A test module is listed next to the unit it tests and follows the rules of that unit. A unit test of `core.matching`, for
example, may import `core.matching` and what lies below it, but no parser binding. Test helpers are listed like any other module.

Two kinds of test code are not checked:

- The feature tests in `features/`: they are end to end and may import from every layer. Import Linter cannot analyse that
  package either, because `features/targets/` holds deliberately malformed Python.
- Test directories without an `__init__.py`, such as `test/tree_sitter/`. Adding one there would shadow the installed
  `tree_sitter` package, because `test/` is on the pytest `pythonpath`.

A test helper must be imported through the `test` package (`from test.c_cpp.factories import Factories`), not through the
pytest `pythonpath` (`from c_cpp.factories import Factories`). Import Linter only sees the first form.

## Running it

```powershell
uv run lint-imports
```

CI runs `uv run lint-imports --no-cache`. Run it from the repository root, so that the `test` package resolves to this
repository and not to the `test` package of the standard library.

Import Linter checks indirect imports as well: in the `layers` contract, a chain of imports through a module that no layer
lists counts as an import. Imports inside an `if TYPE_CHECKING:` block count too.

## Known violations

A known violation is an `ignore_imports` entry of the contract it breaks, with a comment that gives the reason. An entry that no
longer matches an import fails the check, so the list cannot outlive the problems it describes.

Add an entry only when the fix is a design change that does not belong in the pull request at hand. For the
`recipes-without-bindings` contract, the comment names the binding symbol, the capability the core is missing and the issue that
tracks it.

## What it does not check

- That every module is listed in a contract. Import Linter checks this only for layers given as containers, which the current
  package layout does not allow.
- Imports between `ast` and `libcst`, and between libclang and the JSON AST dump: each pair still shares one package.
- That the core contains no language- or parser-specific facts. Review enforces that rule.

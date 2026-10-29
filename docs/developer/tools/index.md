<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Guard rail tools

Guard rail tools safeguard the development of Renaissance.Py.
Each of them encodes a rule that the repository has agreed on, checks it automatically, and fails the build when the rule is broken,
so that a rule stays true instead of slowly eroding.

They are kept in the `tools` package, can all be run locally before a pull request is opened, and are all run again in CI.
Run a tool from the repository root as a module, for example `python -m tools.check_layout`.

The tools are independent of the rest of the repository: they import nothing from `renaissance`, `rejuvenation` or the tests, and
only their own tests in `test/tools` import them. The [layering check](check-layering.md) enforces this. Within `tools`, a tool
may call another tool, and functionality that several tools share lives in `tools/shared`, which holds no tools itself.
`tools/shared/linters.py`, for example, runs `ruff` and `pyright` for the lint budget and for `tools/ruff_stats.py`.

## Available tools

1. [Layering check](check-layering.md) (`lint-imports`, configured in `pyproject.toml`):
   forbids imports that break the dependency rules of the repository structure, in the sources and in the tests.
1. [Layout check](check-layout.md) (`tools/check_layout.py`, configured in `pyproject.toml`):
   requires the tests and the documentation to mirror the code.
1. [Encoding check](check-encoding.md) (`tools/check_encoding.py`):
   requires every file that `git` tracks to be UTF-8, without a byte order mark.
1. [Line ending check](check-line-endings.md) (`tools/check_line_endings.py`):
   requires every text file that `git` tracks to be stored with LF line endings.
1. [Copyright check](check-copyright.md) (`tools/check_copyright.py`):
   checks, inserts and removes the copyright notice of `COPYRIGHT.txt` at the top of every tracked file.
1. [Source root check](check-source-roots.md) (`tools/check_source_roots.py`):
   requires pytest, Ruff and Pyright to list the same source roots in `pyproject.toml`.
1. [Lint and type-check budget](../coding-conventions.md#lint-and-type-check-budgets) (`tools/lint_budget.py`):
   counts the `ruff` and `pyright` issues per kind and fails when a change introduces a new one.
1. [Image policy check](../../documentation-system/enforcement/image-policy-enforcement.md) (`tools/check_doc_images_policy.py`):
   enforces the naming and the location of documentation image assets.

## Adding a guard rail

A new guard rail is worth adding when a rule is stated in the documentation, is easy to break by accident, and can be checked
mechanically. Give it a module in `tools`, tests in `test/tools`, a page in this section, an entry in the list above, and a step
in the appropriate workflow in `.github/workflows`.

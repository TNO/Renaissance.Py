<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Layout check

`tools/check_layout.py` fails the build when the tests or the documentation do not mirror the code: when a unit of code has no
counterpart, or when a test or a page is the counterpart of no unit.

## The rule it enforces

[Repository structure](../architecture/repository-structure.md) decides that the unit tests mirror the source tree, and that
parts of the documentation mirror the source tree and `tools/`. A mirror makes the tests and the documentation of a unit easy
to find, and makes it visible when a unit has none. Checking both directions also catches what a rename leaves behind: a test
directory or a page named after a unit that no longer exists.

## Where the rules live

The mirrors are the `[[tool.check_layout.mirrors]]` tables in `pyproject.toml`; that is their single source of truth.

```toml
[[tool.check_layout.mirrors]]
code = "tools"                          # the directory that holds the units, relative to the repository root
units = "modules"                       # "modules": every .py file directly in `code`, except __init__.py; "packages":
                                        # every directory below `code` that holds an __init__.py
mirror = "test/tools/test_{path}.py"    # the counterpart of a unit; a trailing / makes it a directory
exempt = ["mkdocs_hooks"]               # units without counterpart: known deviations
extra = ["docs/developer/tools/index.md"]   # paths that look like a counterpart, but are not one
```

A unit is named by its path relative to `code`, without `.py`, with `/` between directories: `check_layout` for
`tools/check_layout.py`, `core/matching` for the package `src/renaissance/core/matching/`. The template of `mirror` contains
exactly one placeholder:

| Placeholder    | Is replaced by                        | Example                         |
| -------------- | ------------------------------------- | ------------------------------- |
| `{path}`       | the name of the unit                  | `check_layout`                  |
| `{kebab_path}` | the name of the unit, `_` becomes `-` | `check-layout`, for a page name |

A directory counterpart exists when it holds at least one file; a unit test directory without tests does not count.
The modules of a sub-package, such as `tools/shared/`, are no units of the mirror of `code`; the sub-package gets a mirror of its
own.

A path in the mirror is checked when it has the shape of the template, such as `test/tools/test_*.py`. Helpers such as a
`conftest.py` in `test/tools/` do not have that shape and are left alone. A directory below a mirrored directory, such as a directory
of test data, does have that shape, and is listed in `extra`.

During the migration to the target structure, a mirror is added for each part of `src/renaissance` once that part is in its
target place.

## Running it

```powershell
python -m tools.check_layout
```

`--check` is accepted as well, for symmetry with the other guard rails that CI runs; this check never writes anything.

The files are those that git tracks or would track: `git ls-files --cached --others --exclude-standard`. A new file therefore
counts before it is added, and an ignored file, such as one in `__pycache__`, never counts.

Exit codes:

| Code | Meaning                                                                                  |
| ---- | ---------------------------------------------------------------------------------------- |
| 0    | every unit has its counterpart, and every counterpart its unit                           |
| 1    | at least one violation, including a stale entry of `exempt` or `extra`                   |
| 2    | the configuration is invalid, or the files could not be listed                           |

## Reading its output

Every violation is reported on one line:

```text
The tests and the documentation do not mirror the code:
  tools/check_example.py: has no counterpart test/tools/test_check_example.py
  docs/developer/tools/check-old-example.md: mirrors no unit of tools/
  tools/removed_example: is exempt, but is not a unit: remove the exemption
```

## Known deviations

An entry of `exempt` or `extra` is a known deviation; give it a comment with the reason when that is not obvious. An entry that
no longer describes a deviation fails the check: an exempt unit that has a counterpart or no longer exists, and an extra path that
no longer exists or has become a counterpart. So the lists only shrink.

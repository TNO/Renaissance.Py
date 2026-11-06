<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Name check

`tools/check_names.py` fails the build when a file or directory name does not separate its words by `_`.

## The rule it enforces

[Repository structure](../architecture/repository_structure.md#names) decides that file and directory names separate their words
by a single `_`, never by `-`, and that the test files of a module `x` may be split into `test_x___<aspect>.py`, with a triple
`___` between the module and the aspect.

A separator is a run of underscores between two letters or digits. The check requires of every name that:

- it contains no `-`;
- every separator is a single `_`, or, in a name that starts with `test_`, a triple `___`.

Underscores at the start or the end of a word separate no words, so `__init__.py` passes.

The check looks at names only. Whether `test_x___<aspect>.py` belongs to a module `x` is checked by the
[layout check](check_layout.md).

## Running it

```powershell
python -m tools.check_names
```

`--check` is accepted as well, for symmetry with the other guard rails that CI runs; this check never writes anything.

The names are those of the files that git tracks or would track, `git ls-files --cached --others --exclude-standard`, and of the
directories that hold them. A new file therefore counts before it is added, and an ignored file never counts.

Exit codes:

| Code | Meaning                                    |
| ---- | ------------------------------------------ |
| 0    | every name separates its words by `_`      |
| 1    | at least one name breaks the rule          |
| 2    | the files could not be listed              |

## Reading its output

Every violation is reported on one line; a directory is reported once, not for every file it holds:

```text
These names do not separate their words by `_`:
  docs/bad-example/: contains `-`; separate words by `_`
  tools/check__example.py: separates words by `__`; use `_`
  tools/check___example.py: separates words by `___`, which only a name that starts with `test_` may do
```

## Fixing a reported name

Rename the file or directory with `git mv`, and update the references to it. The [reference check](check_references.md) reports
a reference that still names the old path.

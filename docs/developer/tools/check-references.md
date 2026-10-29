<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Reference check

`tools/check_references.py` fails the build when the documentation, a comment or docstring, or a feature file names a repository
path that does not exist.

## The rule it enforces

Every repository path that is named in the documentation, the code and the tests exists. These references make the link between
a feature, its code, its tests and its pages traceable; a file that moves or disappears must not leave a reference behind.

A path is a name that starts with a top-level directory of the repository followed by `/`, such as `src/renaissance/` or
`docs/index.md`. The check reads:

- the Markdown files in `docs/`;
- the comments and docstrings of the Python files in `src/`, `test/`, `tools/` and `features/`;
- the feature files.

It skips:

- the target of a Markdown link, such as `[Tools](tools/index.md)`: `mkdocs build --strict` checks it, relative to the page;
- a name with a placeholder, a wildcard or an ellipsis, such as `test/unit/{path}/` or `src/*.py`, which names no single file;
- an example: a path with `example` as one of its words, such as `tools/example.py` or `src/example_package/typing.py`.
  Words are separated by `/`, `_`, `-` and `.`, so `test/examples/` is no example. Name a path that only illustrates a point
  this way.

## Where the deviations live

`[tool.check_references]` in `pyproject.toml` lists the known deviations:

```toml
[tool.check_references]
exclude = ["docs/developer/architecture/adr/"]  # files, or directories ending with /, that the check does not read
known_issues = ["src/renaissance/recipes/type_parameter_check.py"]  # missing paths that a known issue explains
stale = ["test/unit/"]  # missing paths that do not exist yet
```

An entry that no longer applies fails the check: a listed path that exists or that no file names any more, and an excluded path
that does not exist. So the lists only shrink. Give a group of entries a comment with its reason.

## Running it

```powershell
python -m tools.check_references
```

`--check` is accepted as well, for symmetry with the other guard rails that CI runs; this check never writes anything.

The files are those that git tracks or would track: `git ls-files --cached --others --exclude-standard`. A path exists when it is
such a file, or a directory that holds one.

Exit codes:

| Code | Meaning                                                                |
| ---- | ---------------------------------------------------------------------- |
| 0    | every named path exists, or is listed as missing                       |
| 1    | at least one violation, including an entry that no longer applies      |
| 2    | the configuration is invalid, or the files could not be listed or read |

## Reading its output

Every violation is reported on one line; a reference with its file and line number:

```text
These references name a missing path, or these entries of [tool.check_references] no longer apply:
  docs/developer/modules/example.md:12: names src/renaissance/example.py, which does not exist
  test/unit/example/: is listed in `stale`, but exists: remove it
```

## Fixing a reported reference

Correct the reference when the path moved, and remove it when the file is gone. Record a missing path in `known_issues` or
`stale` only when the reference is right and the path is missing for a reason, and give that reason.

<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Source root check

`tools/check_source_roots.py` fails the build when pytest, Ruff and Pyright do not list the same source roots in
`pyproject.toml`.

## The rule it enforces

The source roots are the directories that hold the top-level packages, such as `src` for `renaissance`. Pytest, Ruff and Pyright
each need them, in these settings of `pyproject.toml`:

- `[tool.pytest.ini_options] pythonpath`, so the tests can import the packages;
- `[tool.ruff] src`, so Ruff sorts the imports of these packages as first-party;
- `[tool.pyright] extraPaths`, so Pyright resolves the imports of these packages.

All three list the same roots, in the same order. TOML cannot declare the list once and refer to it, so the check keeps the copies
equal: a root added to one setting but not to the others makes the tools disagree about what an import means.

## Running it

```powershell
python -m tools.check_source_roots
```

`--check` is accepted as well, for symmetry with the other guard rails that CI runs; this check never writes anything, so both
invocations behave identically.

Exit codes:

| Code | Meaning                                                               |
| ---- | --------------------------------------------------------------------- |
| 0    | the three settings list the same source roots, in the same order      |
| 1    | the settings differ                                                   |
| 2    | `pyproject.toml` could not be read, or one of the settings is missing |

## Reading its output

When the settings differ, the check lists all three, so the odd one out is easy to spot:

```text
These settings in pyproject.toml must list the same source roots, in the same order:
  [tool.pytest.ini_options] pythonpath = ['src', 'test', 'features']
  [tool.ruff] src = ['src', 'test']
  [tool.pyright] extraPaths = ['src', 'test', 'features']
```

## Fixing a reported setting

Make the three settings equal. A root that one tool needs is needed by all three, so the fix is to add it to every setting, or to
remove it from every setting, rather than to make one setting differ.

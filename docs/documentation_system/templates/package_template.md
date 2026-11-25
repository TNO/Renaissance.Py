<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Package template

{ #template-package }

**Stable ID:** `TEMPLATE-PACKAGE`

The user page of a package, `docs/user/<layer>/<package>/<package>.md`. It describes the public API of the package, which
mkdocstrings renders from the code.

```md
# <Package title>

{ #concept-<layer>-<package> }

**Stable ID:** `CONCEPT-<LAYER>-<PACKAGE>`

## Purpose

## Scope

## Definition

## Invariants / guarantees

## Extension points

## Non-goals

## Related features

## Related tests

## Related code

## API

::: renaissance.<layer>.<package>
    options:
      heading_level: 3
```

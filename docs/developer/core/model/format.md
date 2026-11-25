<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.format

{ #codemod-core-model-format }

**Stable ID:** `CODEMOD-CORE-MODEL-FORMAT`

## Responsibility

The display of a node, with which the core and the parser bindings implement `__repr__`.

## Location

`src/renaissance/core/model/format.py`

## Public entry points

`renaissance.core.model` exports nothing from this module; `format_node` is imported from `renaissance.core.model.format`.

## Internal structure

`format_node` is defined in terms of `display_context` of [`node_utils`](node_utils.md).

## Validated by test modules

None yet.

## Related concepts

- [Core model](../../../user/core/model/model.md)

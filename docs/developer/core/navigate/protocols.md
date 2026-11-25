<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.navigate.protocols

{ #codemod-core-navigate-protocols }

**Stable ID:** `CODEMOD-CORE-NAVIGATE-PROTOCOLS`

## Responsibility

The protocols that a node implements to be navigated.

## Location

`src/renaissance/core/navigate/protocols.py`

## Public entry points

`renaissance.core.navigate` exports `HasParent`, `HasChildren` and `NodeNavigateProtocol`.

## Internal structure

The protocols depend on no other module. The terms and the decisions behind them are in
[Navigation of code](../../architecture/navigation.md).

## Validated by test modules

None yet.

## Related concepts

- [Navigate](../../../user/core/navigate/navigate.md)

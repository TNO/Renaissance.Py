<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# core.model.text_segment

{ #codemod-core-model-text-segment }

**Stable ID:** `CODEMOD-CORE-MODEL-TEXT-SEGMENT`

## Responsibility

The protocol of a consecutive piece of a text, with its offsets, lines and columns.

## Location

`src/renaissance/core/model/text_segment.py`

## Public entry points

`renaissance.core.model` exports `TextSegment`.

## Internal structure

`TextSegment` depends on no other module.

## Validated by test modules

- `test/unit/core/model/test_text_segment.py`

## Related concepts

- [Core model](../../../user/core/model/model.md)

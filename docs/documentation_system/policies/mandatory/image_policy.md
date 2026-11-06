<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Image policy

{ #policy-image-mandatory }

**Stable ID:** `POLICY-IMAGE-MANDATORY`

## Status

This policy is **mandatory**.

## Scope

This policy governs where images are stored, how they are named, and which formats are preferred.

## Storage model

- Use **local image directories** by default for page-specific images.
- Use `docs/assets/images/` for shared, reusable images.

## Allowed locations

### Allowed locations of shared images

- `docs/assets/images/architecture/`
- `docs/assets/images/notation/`
- `docs/assets/images/logos/`

### Allowed locations of local images

- page-owned directories, such as `docs/user/concepts/matching_images/`
- page-owned directories, such as `docs/user/features/pattern_matching_images/`
- page-owned directories for developer-facing pages, such as `docs/developer/architecture/images/`

Page-owned directories **must not** share their name with the sibling page file
(e.g. avoid pairing `matching.md` with a `matching/` directory).
MkDocs builds `<page>.md` and `<page>/README.md` (or `<page>/index.md`)
to the same output path (`<page>/index.html`) when directory URLs are enabled,
so identically named siblings silently overwrite one another in the built site.
Use a distinct suffix such as `_images` instead.

## Naming convention

Image names follow the [naming rule](../../../developer/architecture/repository_structure.md#names) of the repository: their
words are separated by a single `_`. A word consists of lowercase letters (`a–z`) and digits (`0–9`).

### Naming convention for local images

`<page>_<section>_<purpose>.<ext>`

Examples:

- `matching_overview.svg`
- `matching_nested_if_example.svg`
- `matching_greedy_vs_lazy.svg`
- `matching_step2_result.png`

### Naming convention for shared images

`<domain>_<concept>_<variant>.<ext>`

Examples:

- `architecture_overview.svg`
- `notation_placeholder_semantics.svg`

## Preferred formats

- Prefer `svg` for diagrams.
- Use `png` for screenshots.
- Use `jpg` only for photographs.

## Enforcement

- [Image policy enforcement](../../enforcement/image_policy_enforcement.md)
- [CI overview](../../enforcement/ci_overview.md)

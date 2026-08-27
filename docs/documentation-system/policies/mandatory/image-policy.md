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

- page-owned directories, such as `docs/user/concepts/matching-images/`
- page-owned directories, such as `docs/user/features/pattern-matching-images/`
- page-owned directories for developer-facing pages, such as `docs/developer/architecture/images/`

Page-owned directories **must not** share their name with the sibling page file
(e.g. avoid pairing `matching.md` with a `matching/` directory).
MkDocs builds `<page>.md` and `<page>/README.md` (or `<page>/index.md`)
to the same output path (`<page>/index.html`) when directory URLs are enabled,
so identically named siblings silently overwrite one another in the built site.
Use a distinct suffix such as `-images` instead.

## Naming convention

Allowed characters per segment: lowercase letters (`a–z`) and digits (`0–9`).
Segments are separated by hyphens (`-`).
Special characters such as `+`, `_`, spaces, or uppercase letters are not allowed.

### Naming convention for local images

`<page>-<section>-<purpose>.<ext>`

Examples:

- `matching-overview.svg`
- `matching-nested-if-example.svg`
- `matching-greedy-vs-lazy.svg`
- `matching-step2-result.png`

### Naming convention for shared images

`<domain>-<concept>-<variant>.<ext>`

Examples:

- `architecture-overview.svg`
- `notation-placeholder-semantics.svg`

## Preferred formats

- Prefer `svg` for diagrams.
- Use `png` for screenshots.
- Use `jpg` only for photographs.

## Enforcement

- [Image policy enforcement](../../enforcement/image-policy-enforcement.md)
- [CI overview](../../enforcement/ci-overview.md)

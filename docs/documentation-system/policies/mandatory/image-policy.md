{ #policy-image-mandatory }
# Image policy

**Stable ID:** `POLICY-IMAGE-MANDATORY`

## Status

This policy is **mandatory**.

## Scope

This policy governs where images are stored, how they are named, and which formats are preferred.

## Storage model

- Use **local image directories** by default for page-specific images.
- Use `docs/assets/images/` for shared, reusable images.

## Allowed locations

### Shared images
- `docs/assets/images/architecture/`
- `docs/assets/images/notation/`
- `docs/assets/images/logos/`

### Local images
- page-owned directories, such as `docs/user/concepts/matching/`
- page-owned directories, such as `docs/user/features/pattern-matching/`
- page-owned directories for developer-facing pages, such as `docs/developer/architecture/images/`

## Naming convention

### Local images
`<page>-<section>-<purpose>.<ext>`

Examples:
- `matching-overview.svg`
- `matching-nested-if-example.svg`
- `matching-greedy-vs-lazy.svg`

### Shared images
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

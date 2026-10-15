<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Linking policy

{ #policy-linking-mandatory }

**Stable ID:** `POLICY-LINKING-MANDATORY`

## Status

This policy is **mandatory**.

## Scope

This policy governs documentation links and references.

## Requirements

1. Section overviews should link to the pages they introduce.
2. Concept, feature, workflow, and documentation-system overview pages should use navigable links.
3. Internal documentation links should resolve correctly.
4. Image references should point to existing files.
5. Important pages should expose stable anchors where appropriate.

## Recommended linking style

- Prefer relative links within the documentation tree.
- Use stable section anchors for durable references.
- Avoid dead links to repository-external paths from the built documentation site.

## Enforcement

- [Linking policy enforcement](../../enforcement/linking-policy-enforcement.md)
- [CI overview](../../enforcement/ci-overview.md)

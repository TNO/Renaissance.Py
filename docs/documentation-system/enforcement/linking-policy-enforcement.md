<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Linking policy enforcement

This page describes how the mandatory [linking policy](../policies/mandatory/linking-policy.md) is enforced.

## Enforcing tools

The repository includes CI configuration for documentation quality checks:

- `.github/workflows/docs-quality.yml`

The workflow runs checks such as:

- `mkdocs build --strict`
- a documentation link checker workflow step

## Relationship to image checks

The linking policy complements the image policy:

- the linking policy checks that references resolve,
- the image policy checker validates allowed image placement and naming.

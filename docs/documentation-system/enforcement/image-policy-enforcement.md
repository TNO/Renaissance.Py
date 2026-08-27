# Image policy enforcement

This page describes how the mandatory [image policy](../policies/mandatory/image-policy.md) is enforced.

## Enforcing code

The repository contains a custom checker:

- `tools/check_doc_images_policy.py`

This checker validates:

- allowed image locations,
- image file naming conventions,
- supported image filename pattern checks.

## CI integration

The checker is intended to run from CI, for example through:

- `.github/workflows/docs-quality.yml`

## Rationale

Existing generic tools can validate broken links and some Markdown quality aspects, but repository-specific image placement and naming rules are best handled by custom code.

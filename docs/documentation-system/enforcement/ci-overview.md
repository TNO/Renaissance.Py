<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# CI overview

The documentation system can be validated in CI.

## Main enforcement entry point

- `.github/workflows/docs-quality.yml`

## Suggested checks

1. `mkdocs build --strict`
1. documentation link checking
1. image-policy checking via `tools/check_doc_images_policy.py`

## Interpretation

- Mandatory policies should be checked automatically where practical.
- Recommended policies may still require editorial review.

# CI overview

The documentation system can be validated in CI.

## Main enforcement entry point

- `.github/workflows/docs-quality.yml`

## Suggested checks

1. `mkdocs build --strict`
2. documentation link checking
3. image-policy checking via `tools/check_doc_images_policy.py`

## Interpretation

- Mandatory policies should be checked automatically where practical.
- Recommended policies may still require editorial review.

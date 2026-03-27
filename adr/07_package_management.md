# 07 - Use UV for package & environment management

Status: Proposal

Date: 2026-02-25

Authors: Project contributors

## Context

The project uses Python and benefits from reproducible dependency management and straightforward virtual
environment handling. Poetry provides a single-file project manifest (`pyproject.toml`) and an integrated
workflow for dependency resolution, packaging, and environment management.

## Decision

Adopt Poetry as the recommended tool for dependency management and packaging. Encourage contributors to use
Poetry for creating virtual environments, adding/removing dependencies, and building distributions.

## Implementation notes

- Keep `pyproject.toml` and `uv.lock` up-to-date.
- Document common contributor workflows in the repository README (install, run tests, add dependency).
- Provide instructions for creating and activating a Poetry-managed virtualenv and installing dev dependencies.

## Rationale

- Single source of truth (`pyproject.toml`) and dependable lockfile for reproducible builds.
- Simplifies contributor onboarding and packaging.

## Consequences

Positive:
- Reproducible installs and simpler packaging workflows.

Negative:
- Contributors unfamiliar with Poetry need to learn its commands; mitigate with documentation.

## Alternatives considered

- Use pip + virtualenv and `requirements.txt` — rejected for weaker dependency resolution and no standardized
  project manifest.

## Related decisions

- This ADR explains our tooling preference; it does not block using other tools in special cases.


## UV 

UV is the even more modern version, which unifies abstracts all build related tools.
https://github.com/astral-sh/uv

---

Revision history:
- 2026-02-25: Converted to ADR template and clarified decision.

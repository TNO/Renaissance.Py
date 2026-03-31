# 14 - Code Repositories

Status: Proposal

Date: 2026-03-27

Authors:
 - jinmin.hu@capgemini.com
 - huub.joosten@capgemini.com
 - luna.li@capgemini.com
 - paul.nelissen@esi.nl
 - pierre.vandelaar@tno.nl

## Table of contents

- [Context](#context)
- [Decision](#decision)
- [Implementation notes](#implementation-notes)
- [Example](#example)
- [Rationale](#rationale)
- [Consequences](#consequences)
- [Alternatives considered](#alternatives-considered)
- [Related decisions](#related-decisions)

## Context

The project consists of two conceptually distinct layers:

1. **Generic functionality** — the unified AST model, match-pattern engine, rewriter, and other
   language-agnostic components.
2. **Adapters** — language-specific bridges (tree-sitter, Clang, Python 2.x, …) that translate a parser's
   output into the unified AST.

Keeping both layers in a single repository conflates their concerns, complicates licensing (an adapter
author may not want to adopt the same licence as the core), and makes it harder for external contributors
to develop or distribute adapters independently. Repository names must also clearly describe their contents;
names like *rejuvenation* and *renaissance* do not communicate what belongs where.

## Decision

- Maintain **separate repositories** for the generic functionality and for each adapter.
- Repository names must **clearly describe their contents** (e.g., `unified-ast-core`,
  `unified-ast-adapter-treesitter`, `unified-ast-adapter-clang`).
- The names *rejuvenation* and *renaissance* must **not** be used as the distinguishing names between the
  core and adapter packages, as they do not convey their respective responsibilities.
- Plug-in / adapter points beyond parsers (e.g., output formatters, analysis passes) are also eligible for
  their own repositories; evaluate case by case.

## Implementation notes

- Define a stable, versioned **adapter API** (a set of `Protocol` / abstract base classes) in the core
  repository that all adapter repositories must implement.
- Publish the core and each adapter as independent packages on PyPI (or an internal registry) so they can
  be versioned and licensed independently.
- Use the adapter API version as the compatibility contract between core and adapters; bump it on breaking
  changes.
- Document the adapter API in the core repository so external contributors can develop adapters without
  access to the full codebase.

## Example

Proposed repository / package layout:

```
unified-ast-core/              # generic: unified AST, matcher, rewriter, …
unified-ast-adapter-treesitter/  # adapter: tree-sitter → unified AST
unified-ast-adapter-clang/       # adapter: Clang/CDT → unified AST
unified-ast-adapter-python/      # adapter: CPython ast → unified AST
```

Each adapter depends on `unified-ast-core` and implements the `AdapterProtocol`:

```python
# In unified-ast-core
from typing import Protocol

class AdapterProtocol(Protocol):
    def parse(self, source: str) -> AstNode: ...
    def unparse(self, node: AstNode) -> str: ...
```

## Rationale

Separating the core from adapters respects the single-responsibility principle at the repository level,
enables independent licensing (critical for adapters that wrap GPL or proprietary parsers), and lowers the
barrier for external contributors who only need to implement an adapter. Descriptive repository names make
the architecture self-documenting and reduce onboarding friction.

## Consequences

Positive:
- Independent versioning and licensing for core and each adapter.
- External contributors can develop adapters without forking the core.
- Clear repository names make the architecture immediately understandable.
- Smaller, focused repositories are easier to test and review.

Negative:
- More repositories to maintain and keep in sync.
- The adapter API must be carefully designed and versioned to avoid frequent breaking changes.
- Cross-repository CI pipelines require additional setup.

## Alternatives considered

- **Single monorepo** — rejected because it conflates licensing concerns and makes independent adapter
  distribution harder.
- **Keep current names** (*rejuvenation* / *renaissance*) — rejected because they do not describe what
  belongs in each package, causing confusion for contributors.
- **One repo per language** (core bundled with adapter) — rejected because it duplicates the core and
  creates divergence risk.

## Related decisions

- See ADR 07 (Package management) for the tooling used to publish and manage these packages.
- See ADR 03 (Duck typing) for the `Protocol`-based adapter API design.
- See ADR 12 (Patterns are not nodes) and ADR 13 (Match pattern) for the core APIs that adapters must
  produce output for.

---

Revision history:
- 2026-03-27: Converted GitHub issue to ADR template.

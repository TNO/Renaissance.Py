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

The goal of this ADR is to define the repository structure for the Renaissance project, 
balancing modularity, licensing, and contributor accessibility.

**Note:** this structure is a target, not yet realized in the current codebase, which is still a single
repository (`Renaissance.Py`) that has not been split along these lines.

The project consists of four conceptually distinct layers:

1. **Parser-agnostic core** — the unified AST model, match-pattern engine, rewriter, and other
   language- and parser-agnostic components.
2. **Integrations** — parser-specific bridges (tree-sitter, Clang, Python's `ast` module, …) that make a
   parser's native nodes conform to the core's node `Protocol` (see ADR 03). An integration may be
   implemented as a wrapper, an adapter, or by extending the foreign node type directly to satisfy the
   protocol via duck typing (see ADR 06); the choice of technique is an implementation detail internal to
   the integration, not a distinguishing factor at the repository/package level.
3. **Rules** — libraries of shared, basic transformations (e.g., simplifications) that are reused across
   multiple refactorings. The current assumption is one rule library per language, but it may turn out
   that some rules are more naturally scoped per parser/integration instead (e.g., when two integrations
   exist for the same language and expose different behaviours); see [Alternatives considered](#alternatives-considered).
4. **Refactoring examples** — one collection per language, showcasing the capabilities of the software
   through concrete, runnable refactoring examples.

Keeping these layers in a single repository conflates their concerns, complicates licensing (an integration
author may not want to adopt the same license as the core), and makes it harder for external contributors
to develop or distribute integrations, rules, or examples independently. Repository names must also clearly
describe their contents; names like *rejuvenation* and *renaissance* do not communicate what belongs where.

## Decision

- Maintain **separate repositories** for the parser-agnostic core, for each integration, for each rule
  library, and for each collection of refactoring examples.
- Repository names must **clearly describe their contents** (e.g., `unified-ast-core`,
  `unified-ast-integration-treesitter`, `unified-ast-integration-clang`, `unified-ast-rules-python`,
  `unified-ast-examples-python`).
- The names *rejuvenation* and *renaissance* must **not** be used as the distinguishing names between these
  packages, as they do not convey their respective responsibilities.
- Plug-in points beyond parsers (e.g., output formatters, analysis passes) are also eligible for their own
  repositories; evaluate case by case.
- Whether rule libraries are scoped per language or per integration/parser is not yet decided; start from
  one rule library per language and revisit if evidence shows rules need to diverge per integration.

## Implementation notes

- Define a stable, versioned **integration API** (a set of `Protocol` / abstract base classes) in the core
  repository that all integration repositories must satisfy.
- Publish the core, each integration, each rule library, and each examples collection as independent
  packages on PyPI (or an internal registry) so they can be versioned and licensed independently.
- Use the integration API version as the compatibility contract between core and integrations; bump it on
  breaking changes.
- Document the integration API in the core repository so external contributors can develop integrations
  without access to the full codebase.
- Rule libraries and examples depend on the core (and, if scoped per integration, on that integration) but
  the core must never depend on them.

## Example

Proposed repository / package layout:

```
unified-ast-core/                  # parser-agnostic: unified AST, matcher, rewriter, …
unified-ast-integration-treesitter/  # integration: tree-sitter → unified AST
unified-ast-integration-clang/       # integration: Clang/CDT → unified AST
unified-ast-integration-python/      # integration: CPython ast → unified AST
unified-ast-rules-python/            # rules: shared simplifications/transformations for Python
unified-ast-rules-cpp/               # rules: shared simplifications/transformations for C++
unified-ast-examples-python/         # examples: refactoring examples showcasing Python support
unified-ast-examples-cpp/            # examples: refactoring examples showcasing C++ support
```

Each integration depends on `unified-ast-core` and implements the `IntegrationProtocol`:

```python
# In unified-ast-core
from typing import Protocol

class IntegrationProtocol(Protocol):
    def parse(self, source: str) -> AstNode: ...
    def unparse(self, node: AstNode) -> str: ...
```

## Rationale

Separating the core from integrations, rules, and examples respects the single-responsibility principle at
the repository level, enables independent licensing (critical for integrations that wrap GPL or proprietary
parsers), and lowers the barrier for external contributors who only need to implement an integration, a rule
library, or a set of examples. Descriptive repository names make the architecture self-documenting and
reduce onboarding friction. Naming the second layer "integrations" rather than "adapters" or "wrappers"
avoids implying a single technique — wrappers, adapters, and duck-typed extensions (ADR 06) are all valid
ways to integrate a parser, and the repository/package boundary should not force a choice between them.

## Consequences

Positive:
- Independent versioning and licensing for core, integrations, rules, and examples.
- External contributors can develop integrations, rules, or examples without forking the core.
- Clear repository names make the architecture immediately understandable.
- Smaller, focused repositories are easier to test and review.

Negative:
- More repositories to maintain and keep in sync.
- The integration API must be carefully designed and versioned to avoid frequent breaking changes.
- Cross-repository CI pipelines require additional setup.
- Whether rules are scoped per language or per integration is undecided, so the rules layer may need to be
  restructured once that is resolved.

## Alternatives considered

- **Single monorepo** — rejected because it conflates licensing concerns and makes independent
  integration, rules, and examples distribution harder.
- **Keep current names** (*rejuvenation* / *renaissance*) — rejected because they do not describe what
  belongs in each package, causing confusion for contributors.
- **One repo per language** (core bundled with integration, rules, and examples) — rejected because it
  duplicates the core and creates divergence risk.
- **Rules scoped per integration/parser instead of per language** — not rejected, but deferred: if a
  language has multiple integrations with diverging behaviours, a single per-language rule library may
  not be reusable across all of them. Revisit once multiple integrations exist for the same language.

## Related decisions

- See ADR 07 (Package management) for the tooling used to publish and manage these packages.
- See ADR 03 (Duck typing) and ADR 06 (Wrapper or adapter) for the techniques an integration may use to
  satisfy the core's node `Protocol`.
- See ADR 12 (Patterns are not nodes) and ADR 13 (Match pattern) for the core APIs that integrations must
  produce output for.

---

Revision history:
- 2026-03-27: Converted GitHub issue to ADR template.
- 2026-09-02: Renamed "generic functionality" to "parser-agnostic core" and "adapters" to "integrations"
  (to cover wrappers, adapters, and duck typing alike); added rules and refactoring-examples layers.

# 14 - Code Repository Structure

Status: Accepted

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

The goal of this ADR is to define the repository and directory structure for the Renaissance project,
balancing modularity, licensing, and contributor accessibility.

The project consists of four conceptually distinct layers:

1. **Renaissance** — the parser-agnostic core: the unified AST model, match-pattern engine, rewriter, and
   other language- and parser-agnostic components.
2. **Integrations** — parser-specific bridges (tree-sitter, Clang, Python's `ast` module, …) that make a
   parser's native nodes conform to the core's node `Protocol` (see ADR 03). An integration may be
   implemented as a wrapper, an adapter, or by extending the foreign node type directly to satisfy the
   protocol via duck typing (see ADR 06); the choice of technique is an implementation detail internal to
   the integration, not a distinguishing factor at the directory level.
3. **Recipes** — libraries of shared transformations, reused across multiple rejuvenations. A recipe is
   more powerful than a single find / filter / modify rule: it combines multiple such rules in a smart way
   to perform a non-trivial, composite transformation. The current assumption is one recipe library per
   language, but it may turn out that some recipes are more naturally scoped per parser/integration instead
   (e.g., when two integrations exist for the same language and expose different behaviours); see
   [Alternatives considered](#alternatives-considered).
4. **Rejuvenations** — one collection per language of concrete, runnable applications of Renaissance,
   responding to change that originates from the customer (changed requirements), the organization
   (business strategy, process, or structure), or the environment (dependency/tooling versions). Instances
   include transpilation, migrations (language, dependency, or tooling version), and educational examples.

Separating these layers' concerns, and making licensing per contribution explicit, matters most for the
integrations layer: an integration author may need to wrap a GPL or proprietary parser under a license
different from the core's, and third parties should be able to add a new integration (or recipe library, or
rejuvenation collection) without needing write access to, or forking, the rest of the project.

We considered achieving this by splitting the project into **separate repositories** — one per core,
integration, recipe library, and rejuvenation collection. We rejected that: with an expected handful of
integrations, recipe libraries, and rejuvenation collections per language, a multi-repository layout would
force users and contributors to discover, clone, and version-align many small repositories to get a working
setup, which is harder to understand than a single entry point. Instead, we keep **one repository (one
archive)** and make its directory structure **extendable**, so third parties can contribute a layer instance
as a new subdirectory, alongside existing ones, without touching the core.

## Decision

- Keep the project as **one repository (archive)** — the existing `Renaissance.Py` repository. Do not split
  Renaissance, integrations, recipe libraries, or rejuvenation collections into separate repositories.
- Structure the repository so that each extendable layer (today: integrations) is a directory containing
  **one subdirectory per contribution** (e.g., one subdirectory per parser integration). Adding a new
  contribution means adding a new subdirectory alongside the existing ones — it must not require changes to
  the core or to other contributions.
- Directory names must **clearly describe their contents**, following the same naming convention as the
  conceptual layers: `renaissance` (the core), `integrations/<parser>` (one per parser), `recipes/<language>`
  (one per language, see [Alternatives considered](#alternatives-considered) on per-integration scoping),
  and `rejuvenation/<language>` (one per language).
- Each contribution subdirectory **may carry its own license**, distinct from the repository's overall
  license, using a `LICENSE` file and/or SPDX license headers scoped to that subdirectory. This is required
  when an integration wraps a GPL or proprietary parser.
- Plug-in points beyond parsers (e.g., output formatters, analysis passes) are also eligible for their own
  subdirectory under the appropriate extendable layer; evaluate case by case.
- Whether recipe libraries are scoped per language or per integration/parser is not yet decided; start from
  one recipe library per language and revisit if evidence shows recipes need to diverge per integration.

## Implementation notes

- Define a stable, versioned **integration API** (a set of `Protocol` / abstract base classes) in
  `renaissance` that all integration subdirectories must satisfy.
- Declare per-integration dependencies (e.g., `clang`, `tree-sitter`) as optional dependency groups /
  extras (see ADR 07), so that installing the package does not force every user to pull in every parser's
  dependencies.
- Use the integration API version as the compatibility contract between the core and integrations; bump it
  on breaking changes.
- Document the integration API in `renaissance` so external contributors can develop an integration
  subdirectory without needing to understand the rest of the codebase.
- Track the license of each contribution subdirectory explicitly (a `LICENSE` file in the subdirectory, or
  SPDX `SPDX-License-Identifier` headers in its files) so that a subdirectory's license is unambiguous even
  though the repository as a whole is not single-licensed.
- Recipe libraries and rejuvenations depend on `renaissance` (and, if scoped per integration, on that
  integration) but `renaissance` must never depend on them.

## Example

Current directory layout, within the single `Renaissance.Py` repository:

```text
Renaissance.Py/                       # one repository (archive)
  src/
    renaissance/                      # parser-agnostic core: unified AST, matcher, rewriter, …
      integrations/                  # "integrations" layer: one subdirectory per parser
        python/                      # integration: CPython-based parsing → unified AST
          ast/                       # parser option: stdlib `ast` module (other python parsers are
                                     # possible siblings here, e.g. a future `cst/` using `libcst`)
        tree_sitter/                 # integration: tree-sitter → unified AST
        clang/                       # integration: Clang/CDT → unified AST
        <third-party-parser>/        # a third party adds their integration here, own LICENSE allowed
      recipes/                       # "recipes" layer: shared transformations reused across rejuvenations
    rejuvenation/                    # "rejuvenations" layer: refactorings, migrations, transpilations, examples
```

Each integration subdirectory depends on `renaissance` and implements the `IntegrationProtocol`:

```python
# In renaissance
from typing import Protocol

class IntegrationProtocol(Protocol):
    def parse(self, source: str) -> AstNode: ...
    def unparse(self, node: AstNode) -> str: ...
```

## Rationale

A single repository keeps discovery, cloning, installation, and versioning simple for both users and
contributors — there is exactly one place to look, one CI pipeline, and one version to check out. Making the
extendable layers directory-based, with one subdirectory per contribution, still gives third parties an
isolated place to add an integration, a recipe library, or a rejuvenation collection — via a pull request
adding a subdirectory — without needing to coordinate with, fork, or gain write access to the rest of the
project. Allowing a per-subdirectory license addresses the licensing concern that originally motivated
splitting into separate repositories: an integration that wraps a GPL or proprietary parser can carry its
own `LICENSE`/SPDX header without requiring the whole repository (or even the whole integrations layer) to
adopt that license. Naming the third layer "recipes" rather than "rules" reflects that a recipe combines
multiple simple rules into a coordinated, more powerful transformation, rather than being limited to a
single find / filter / modify rule. Naming the fourth layer "rejuvenations" rather than "examples" reflects
that this layer's collections range far beyond illustrative examples, covering real refactorings driven by
customer, organizational, and environmental change — of which educational examples are only one instance.

## Consequences

Positive:

- A single clone, install, and version to reason about — simpler for users and new contributors than a
  multi-repository layout.
- Third parties can still add an integration, a recipe library, or a rejuvenation collection as a new
  subdirectory, without forking or gaining write access to the rest of the project.
- Per-subdirectory licensing accommodates integrations that must wrap GPL or proprietary parsers, without
  requiring separate repositories.
- One CI pipeline covers the whole project; no cross-repository version alignment is needed.

Negative:

- The repository grows over time as more integrations, recipe libraries, and rejuvenation collections are
  added; it cannot be checked out or built "a la carte" the way separate repositories could.
- Mixed licensing within one repository must be tracked carefully per subdirectory (via `LICENSE` files
  and/or SPDX headers) to remain unambiguous.
- Per-integration dependencies must be modeled as optional extras so that installing the package does not
  force every user to pull in every parser's dependencies.
- Whether recipes are scoped per language or per integration is undecided, so the recipes layer may need to
  be restructured once that is resolved.

## Alternatives considered

- **Separate repositories per layer instance** (one for the core, one per integration, one per recipe
  library, one per rejuvenation collection) — reconsidered and rejected in favor of a single, extendable
  repository: with the expected number of integrations, recipe libraries, and rejuvenation collections per
  language, a multi-repository layout adds discovery and version-alignment overhead for users without a
  proportional licensing benefit, since per-subdirectory licensing addresses the licensing concern within a
  single repository.
- **Single monorepo without an extendable structure** — rejected because it would force third parties to
  modify shared code/directories to add an integration, recipe library, or rejuvenation collection, instead
  of contributing an isolated new subdirectory.
- **One repo per language** (Renaissance bundled with integration, recipes, and rejuvenations) — rejected
  because it duplicates the core and creates divergence risk.
- **Recipes scoped per integration/parser instead of per language** — not rejected, but deferred: if a
  language has multiple integrations with diverging behaviours, a single per-language recipe library may
  not be reusable across all of them. Revisit once multiple integrations exist for the same language.
- **"Examples" as the name for the fourth layer** — rejected: it undersells the layer's quality and
  complexity, since rejuvenations range from real customer-, organization-, and environment-driven change
  to transpilation and migration, of which educational examples are only one instance.

## Related decisions

- See ADR 07 (Package management) for the tooling used to publish and manage optional per-integration
  dependencies.
- See ADR 03 (Duck typing) and ADR 06 (Wrapper or adapter) for the techniques an integration may use to
  satisfy the core's node `Protocol`.
- See ADR 12 (Patterns are not nodes) and ADR 13 (Match pattern) for the core APIs that integrations must
  produce output for.

---

Revision history:

- 2026-03-27: Converted GitHub issue to ADR template.
- 2026-03-28: Executed the rename to match this ADR: `src/renaissance/impl/` → `src/renaissance/integrations/`,
  `src/renaissance/refactoring/` → `src/renaissance/recipes/` (with matching renames under `test/`), and
  nested the Python integration one level deeper as `integrations/python/ast/` to name the specific parser
  option (stdlib `ast`) used, leaving room for sibling parser options under `integrations/python/`. Status
  changed to Accepted; this ADR now describes the current codebase, not a future target.
- 2026-09-02: Renamed "generic functionality" to "parser-agnostic core" and "adapters" to "integrations"
  (to cover wrappers, adapters, and duck typing alike); added rules and refactoring-examples layers.
- 2026-09-03: Named the parser-agnostic core layer "Renaissance", renamed "rules" to "recipes" (a recipe
  combines multiple rules), and renamed "refactoring examples" to "rejuvenations" (a broader layer covering
  requirement-, business-, transpilation-, and migration-driven change, of which examples are only one
  instance). Removed the claim that the names *rejuvenation* and *renaissance* do not communicate what
  belongs where, since this ADR now assigns them clear, dedicated meanings.
- 2026-09-03: Reversed the "separate repositories per layer" decision: keep a single repository (archive) to
  avoid overwhelming users with too many repositories, and instead make the directory structure extendable
  (one subdirectory per integration/recipe library/rejuvenation collection, each allowed its own license) so
  third parties can still contribute independently.

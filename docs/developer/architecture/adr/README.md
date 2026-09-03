# Architecture Decision Records

This directory contains all Architecture Decision Records (ADRs) for the Renaissance project.
Each ADR documents a significant design or technology choice, its context, rationale, and consequences.

The goal of ADR is to give the developer of new language AST for Renaissance a guideline on:

* how to make correct design choice coherent to the ADR during the implementation and gives
  rationale on why each decision are made.
* minimize the effort for the developer of the new language for renaissance.
* provide  insight to the design and evolution of the project for developer of new language and
  future maintainers and contributors.

## Index

| #                                         | Title                                                  | Status   |
|-------------------------------------------|--------------------------------------------------------|----------|
| [01](01_children_and_properties.md)       | Children and properties                                | Accepted |
| [02](02_direct_access.md)                 | Direct access to fields                                | Accepted |
| [03](03_duck_typing.md)                   | Duck typing for nodes                                  | Accepted |
| [04](04_immutable_properties.md)          | Make nodes immutable                                   | Proposal |
| [05](05_buildin_functions.md)             | Use Python's built-in dunder methods for node behavior | Proposal |
| [06](06_wrapper_or_adapter.md)            | Wrapper or adapter for external node shapes            | Proposal |
| [07](07_package_management.md)            | Use UV for package & environment management            | Proposal |
| [08](08_pytest_suite.md)                  | Test Architecture                                      | Accepted |
| [09](09_property_based_tests.md)          | Property-Based Tests                                   | Proposal |
| [10](10_type_hierarchy.md)                | Type Hierarchy                                         | Proposal |
| [11](11_parser_with_space_and_comment.md) | Parser with Space and Comment                          | Proposal |
| [12](12_patterns_as_not_nodes.md)         | Patterns Are Not Nodes                                 | Proposal |
| [13](13_match_pattern.md)                 | Match Pattern                                          | Proposal |
| [14](14_code_repositories.md)             | Code Repository Structure: Core, Integrations, Recipes, Rejuvenations | Accepted |

## ADR template

Each ADR follows this structure:

```text
# <number> - <title>
Status: Proposal | Accepted | Deprecated | Superseded
Date: YYYY-MM-DD
Authors: ...
## Table of contents
## Context
## Decision
## Implementation notes
## Example
## Rationale
## Consequences
## Alternatives considered
## Related decisions
---
Revision history:
```

---
Revision history:

* 2026-03-27: Created index.
* 2026-03-27: Added ADR 12 (Patterns Are Not Nodes).
* 2026-03-27: Added ADR 13 (Match Pattern) and ADR 14 (Code Repositories).
* 2026-09-02: Updated ADR 14 title to reflect the rules and refactoring-examples layers.
* 2026-09-03: Updated ADR 14 title to reflect the single-repository, extendable directory structure
  decision (renamed "rules" to "recipes" and "refactoring examples" to "rejuvenations").

# Guard rail tools

Guard rail tools safeguard the development of Renaissance.Py.
Each of them encodes a rule that the repository has agreed on, checks it automatically, and fails the build when the rule is broken,
so that a rule stays true instead of slowly eroding.

They are kept in the `tools` directory, can all be run locally before a pull request is opened, and are all run again in CI.

## Available tools

1. [Layering check](check-layering.md) (`tools/check_layering.py`):
   forbids imports that cross a layer boundary, which keeps the core independent of the parser bindings and the recipes.
1. [Lint and type-check budget](../coding-conventions.md#lint-and-type-check-budgets) (`tools/lint_budget.py`):
   counts the `ruff` and `pyright` issues per kind and fails when a change introduces a new one.
1. [Image policy check](../../documentation-system/enforcement/image-policy-enforcement.md) (`tools/check_doc_images_policy.py`):
   enforces the naming and the location of documentation image assets.

## Adding a guard rail

A new guard rail is worth adding when a rule is stated in the documentation, is easy to break by accident, and can be checked
mechanically. Give it a script in `tools`, tests in `test/tools`, a page in this section, an entry in the list above, and a step in
the appropriate workflow in `.github/workflows`.

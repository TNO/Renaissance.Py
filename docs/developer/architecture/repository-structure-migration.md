<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Repository structure migration

{ #dev-architecture-repository-structure-migration }

**Stable ID:** `ARCH-CODE-STRUCTURE-MIGRATION`

**Status:** Draft, for [issue 187](https://github.com/TNO/Renaissance.Py/issues/187).

## Purpose

Plan the moves that bring the repository from its current layout to the [repository structure](repository-structure.md),
in small steps that each leave the repository working.

## Scope

This page describes the order of the moves, what each step moves, and how to check that a step is done.
It does not describe the target structure; that is the [repository structure](repository-structure.md).
It does not fix violations of that structure: the migration moves code, and records each violation that remains.
The last step removes this page; git keeps its history.

## Definition

### Principles

- **Move, then fix.** A step moves code and updates its importers. It does not change behaviour and introduces no new
  abstractions. A violation that a step makes visible is recorded: as an `ignore_imports` entry with its reason, or under
  [Known violations](repository-structure.md#known-violations). Once the migration is done, each known violation gets an issue.
- **Bottom up.** The core moves first, sub-package by sub-package, from `core.model` up to `core.processing`;
  then the parser bindings; then the recipes; then the tests that are not unit tests.
  Within a sub-package, a module moves before the modules that import it.
- **No compatibility shims.** A step updates every importer, in `src/`, `test/` and `features/`, so the old module disappears
  in the same step. Each symbol is defined in exactly one place at every commit.
- **The rules move with the code.** A step replaces the old module names in `[tool.importlinter]` by the new package, adds the
  `protected` contract of each new package, and adds the mirrors of each new package to `[tool.check_layout]`.
  Import Linter fails on an `ignore_imports` entry that matches no import, so a stale entry cannot remain.
- **Tests move with their unit.** A unit test moves to the directory of the unit it tests, not of the parser it happens to use.
  Where a test's unit is not obvious from its name, the step decides on what the test asserts, and records the decision in its
  commit message.
- **Test helpers are shared at the level of their users.** A test helper, such as a test double or a factory, lives in a
  `shared/` directory, as `tools/shared/` does for the tools: in the lowest directory that contains all the tests that use it.
  A helper that only tests of the core model use goes to `test/unit/core/model/shared/`; a helper that unit tests of several
  layers use goes to `test/unit/shared/`. A helper moves with the first of its users that moves, to the lowest directory that
  contains the destinations of all its users; this plan gives these destinations. A helper follows the dependency rules of the
  directory it lives in; its imports that break the rules of its users are known violations, as they are today. Each `shared/`
  directory is an `extra` of the test mirror in `[tool.check_layout]`.
- **Traceability is kept, and improved.** A step updates every reference to a path it moves: in the documentation, in
  docstrings and comments, in feature files and in `docs/developer/feature-test-map/`. The guard rail of step 0.1 checks that
  every referenced path exists. The mirrors make the link between a package, its tests and its pages structural, and the page
  of each package names its tests and its features.
- **One step, one commit, pushed.** Files are moved with `git mv` and keep most of their content, so that git detects the
  rename and `git log --follow` shows their history. Each commit is pushed to `origin`, to the branch of issue 187.
- **One pull request.** The whole migration is reviewed and merged as one pull request. Other open pull requests rebase onto
  it; because git detects the renames, a rebase carries their changes over to the moved files.

### Substeps

Every step consists of the same four substeps, in this order.

1. **src:** move the modules with `git mv`, split a module where the step says so, write the `__init__.py` of each new package
   (its `__all__` and the imports of these symbols, nothing else), and update the imports in `src/`.
1. **test:** move the unit tests with `git mv` to the mirror of their unit under `test/unit/`, add the `__init__.py` files,
   and update the imports in `test/` and `features/`.
1. **docs:** add the mirror pages of each new package (`docs/developer/modules/`, `docs/developer/api/`, and for the core and the
   recipes `docs/user/`), add them to the `mkdocs.yml` nav, and update
   [repository structure](repository-structure.md): the *now in* column, and the paths under Known violations.
   A page in `docs/developer/modules/` follows the [code module template](../../documentation-system/templates/code-module-template.md):
   its *Location*, *Validated by test modules* and *Related features* name the package, its test directory and its features.
   A page in `docs/developer/api/` renders the package with mkdocstrings, so the strict build fails when the package is missing.
   Existing pages that are organised by topic, such as `docs/developer/modules/matching.md`, stay; content that describes the
   moved package moves to its mirror page.
   Update every reference to a moved path: in the documentation, in `docs/developer/feature-test-map/`, and in docstrings,
   comments and feature files.
1. **remaining:** update `[tool.importlinter]`, `[tool.check_layout]`, `[tool.check_references]` and any other path in
   `pyproject.toml`, the CI workflows
   and the repository memory; run the gate; commit; push to `origin`.

### Gate

A step is done when each of the following commands exits with 0, run from the repository root in the activated virtual
environment.

- Tests: `python -m pytest -q -p no:cacheprovider`, with the same counts as after the previous step.
- Layering: `uv run lint-imports --no-cache`.
- Layout: `python -m tools.check_layout`.
- References: `python -m tools.check_references`, from step 0.1 on.
- Source roots: `python -m tools.check_source_roots`, which matters from step 8.1 on, when the feature tests move.
- Lint: `ruff check src test tools features` and `ruff format --check src test tools features`.
- Lint budget: `python -m tools.lint_budget --check`. No budget is raised.
- Copyright, encoding and line endings: `python -m tools.check_copyright check`, `python -m tools.check_encoding --check` and
  `python -m tools.check_line_endings --check`.
- Spelling: `uv run codespell ./src ./test ./tools ./features ./docs`.
- Markdown and documentation: `uv run pymarkdown scan -r --respect-gitignore .`, `python -m tools.check_doc_images_policy` and
  `uv run mkdocs build --strict`.
- History: `git show -M --stat HEAD` shows each moved file as a rename.

In addition, each step has its own checks, listed with the step. A check of the form *`git grep X` finds nothing* covers
`src/`, `test/`, `features/`, `docs/` (except `docs/developer/architecture/adr/`, which records history), `pyproject.toml`,
`mkdocs.yml` and `.github/`.

### Test helpers

The helpers that exist today, with their users, their destination and the step that moves them.

- `test/syntax_tree/infra_text_segment.py` and `infra_syntax_node.py`: used only by the tests of the text segments, so they go
  to `test/unit/core/model/shared/` in step 1.2.
- `test/c_cpp/factories.py`: used by tests of the core, of the clang bindings, of `cleanup_refactoring` and of the examples, so
  it goes to `test/unit/shared/`, with the first of its users that moves: in step 1.5 if `test_ast_factory.py`,
  `test_ast_finder.py` or `test_ast_references.py` moves to the core model, else in step 3.1 or 4.2.
  The test input `features/targets/pyunit_test_example.py` names it too, but test inputs are not changed.
- `test/utils_for_tests.py`: used by `test_ast_rewriter.py`, `test_c_match_finder.py` and two tests of the Python bindings, so
  it goes to `test/unit/shared/`, in step 3.1 if `test_c_match_finder.py` moves to the matching, else in step 4.2.
- `test/utils/util_equivalence_classes.py`: used by three matcher tests in `test/python/ast/`. Step 3.1 decides whether they
  test the matching or a binding, and the helper goes to the `shared/` directory of that unit in the same step.
- `test/python/ast/factories.py`: used by `test_python_nodes.py` and `test_python_pattern_factory.py`, so it goes to the
  `shared/` directory of the Python binding tests in step 6.4.
- `test/search_strategies/python_type_and_value.py`: used only by its own tests; see step 8.2.

### Steps

Each step lists what is particular to it; the substeps that are the same for every step are not repeated.
Paths in a *src* substep are relative to `src/renaissance/`, unless they start with `src/`. A file name without a directory is
in the same directory as the path before it.

#### Phase 0: preparation

**0.1 Check the references between documents, code and tests.**

- src: a new guard rail `tools/check_references.py`, with one rule: every repository path that is named in the documentation,
  in a docstring or comment of `src/`, `test/`, `tools/` or `features/`, or in a feature file, exists. A path is a name that
  starts with a top-level directory of the repository, such as `src/` or `docs/`. It skips the targets of Markdown links, which
  `mkdocs build --strict` checks, and examples: paths with `example` as one of their words. `list_files` and `with_directories`
  move from `tools/check_layout.py` to `tools/shared/repository_files.py`, because both checks use them.
- test: `test/tools/test_check_references.py`; the test of `list_files` moves to `test/tools/shared/test_repository_files.py`.
- docs: `docs/developer/tools/check-references.md`, its entry in the tools index and in the `mkdocs.yml` nav. The paths that
  only illustrate a point are renamed to examples.
- remaining: `[tool.check_references]` in `pyproject.toml`. `exclude` lists the decision records in
  `docs/developer/architecture/adr/`, which record history, and this page, which names the paths the migration creates.
  `known_issues` lists the files of type parameter modernization, which is documented but whose code is not yet integrated.
  `stale` lists the paths that do not exist yet, such as `test/unit/`; the step that creates such a path removes its entry.
  The lists only shrink. A step in the code quality workflow.
- Checks: `python -m tools.check_references` passes, and fails on a reference to a path that does not exist.

**0.2 Remove the re-exports of `renaissance.syntax_tree`.**

- src: `syntax_tree/__init__.py` keeps its docstring only. The importers of its 21 names, including `CPPUtils`, `TextUtils` and
  `ASTRefactorActions`, import from the defining module instead. This removes the late import that works around the circular
  import with `integrations.clang`.
- test: the same for the importers in `test/` and `features/`.
- remaining: remove the two `ignore_imports` entries for the re-exports from the `layers` contract.
- Checks: `git grep -E "from renaissance\.syntax_tree import"` finds nothing; `test_removed_legacy_api` still passes.

**0.3 Create the core.**

- src: `src/renaissance/core/__init__.py`, with a docstring only: the core exports nothing from its root.
- test: `test/unit/__init__.py` and `test/unit/core/__init__.py`.
- remaining: four mirrors of `src/renaissance/core` with `units = "packages"`: `test/unit/core/{path}/`,
  `docs/developer/modules/core/{kebab_path}.md`, `docs/developer/api/core/{kebab_path}.md` and `docs/user/core/{kebab_path}.md`.
- Checks: `python -m tools.check_layout` lists the four new mirrors, with no units yet.

#### Phase 1: `core.model`

The modules of this phase move to `core/model/`, their tests to `test/unit/core/model/`.

**1.1 The vocabulary.**

- src: `syntax_tree/semantic_kind.py` and `node_protocol.py`.
- test: `test/syntax_tree/test_node_protocol.py`. Its import of `match_finder` remains a known violation.
- remaining: the `protected` contract of `core.model`, which every later step of this phase keeps.

**1.2 The text segments.**

- src: `syntax_tree/text_segment.py`, `syntax_node.py` and `siblings.py`.
- test: `test/syntax_tree/test_text_segment.py` and `test_syntax_node.py`. Only these tests use the test doubles
  `infra_text_segment.py` and `infra_syntax_node.py`, so they move to `test/unit/core/model/shared/`.

**1.3 The text utilities.**

- src: `utils/text_utils.py`. Two of its functions leave the core and become internal to their only user:
  `signature_to_id` to `integrations/tree_sitter/visualizer.py`, and `snake_case` to `recipes/python_refactoring.py`.
- test: `test/utils/test_text_utils.py`.

**1.4 The node utilities.**

- src: from `utils/ast_utils.py`, `traverse`, `display_context` and `process_node` to `core.model`, and `preceding_sibling`,
  `next_sibling`, `match_props`, `match_children` and `format_node` to `core.model.for_bindings`.
  From `integrations/python/ast/util.py`, `convert` to `core.model.for_bindings`, and `to_str` to
  `recipes/python_refactoring.py` (internal).
  `replace_dollar`, `use_dollar` and `detect_placeholder` are all that is left in `utils/ast_utils.py`.
- remaining: the `protected` contract of `core.model.for_bindings`, which allows the core, `renaissance.integrations`,
  `renaissance.project` and their tests. The allowed importers follow the bindings as they move.

**1.5 The nodes.**

- src: `syntax_tree/ast_node.py`, `ast_factory.py`, `ast_finder.py` and `ast_shower.py`.
- test: `test/syntax_tree/test_node_finder.py`, `test_semantic_finder.py` and `test_removed_legacy_api.py`; and, if they test
  the model rather than a binding, `test/c_cpp/test_ast_factory.py`, `test_ast_finder.py`, `test_astshower.py`,
  `test_ast_references.py` and `test/python/ast/test_python_astshower.py`. Their imports of a binding become known violations.
- Checks: `git grep -E "utils\.text_utils|syntax_tree\.(semantic_kind|node_protocol|text_segment|syntax_node|siblings)"` and
  `git grep -E "syntax_tree\.ast_(node|factory|finder|shower)"` find nothing; the model layer of the `layers` contract is
  `renaissance.core.model` and its tests.

#### Phase 2: `core.pattern`

The modules of this phase move to `core/pattern/`, their tests to `test/unit/core/pattern/`.

**2.1 The pattern language.**

- src: `syntax_tree/pattern_kind.py`. To `core.pattern.for_bindings`: `MATCH_ONE` and `MATCH_ALL` from
  `integrations/__init__.py`, `replace_dollar`, `use_dollar` and `detect_placeholder` from `utils/ast_utils.py`, and
  `pattern_kind` from `syntax_tree/match_finder.py`.
- test: `test/syntax_tree/test_pattern_kind.py`.
- remaining: the known violation `renaissance.utils.ast_utils -> renaissance.integrations` disappears, because the markers are
  parser agnostic and now live in the core; remove its `ignore_imports` entry.
- Checks: `src/renaissance/utils/` no longer exists; `integrations/__init__.py` defines nothing.

#### Phase 3: `core.matching`

The modules of this phase move to `core/matching/`, their tests to `test/unit/core/matching/`.

**3.1 The matcher.**

- src: `syntax_tree/match_finder.py`; `find_in_list` to `core.matching.for_bindings`.
- test: `test/syntax_tree/test_match_finder.py`, `test_match_finder_multi_assignments.py`, `test_match_tree.py`,
  `test_match_dict.py` and `test_pattern_match.py`.
  The matcher tests under `test/c_cpp/`, `test/python/ast/`, `test/lst/` and `test/tree_sitter/` move here if they test the
  algorithm, and stay with their binding if they test how the binding presents its nodes to the matcher.
  This decides the users of `test/utils/util_equivalence_classes.py`, which moves to their `shared/` directory.
- Checks: `git grep "syntax_tree.match_finder"` finds nothing.

#### Phase 4: `core.rewriting`

The modules of this phase move to `core/rewriting/`, their tests to `test/unit/core/rewriting/`.

**4.1 The character-based rewriter.**

- src: `common/rewriter.py`.
- test: `test/common/test_rewriter.py`.
- Checks: `src/renaissance/common/` and `test/common/` no longer exist.

**4.2 The node-based rewriter.**

- src: `syntax_tree/ast_rewriter.py`.
- test: `test/syntax_tree/test_ast_rewriter.py` and `test_rewrite_semantics_properties.py`, and the helpers of
  `test_ast_rewriter.py` that have not moved yet; see [Test helpers](#test-helpers).
- remaining: the `ignore_imports` entries of the Python binding tests that check the effect of a rewrite follow the new path.

#### Phase 5: `core.processing`, and closing the core

**5.1 The processors.**

- src: `syntax_tree/ast_processor.py`, `batch_ast_processor.py` and `recipe_ast_processor.py` to `core/processing/`.
- test: `test/syntax_tree/test_ast_processor.py`, `test_ast_processor_semantic_kind.py`, `test_batch_ast_processor.py` and
  `test_recipe_ast_processor.py` to `test/unit/core/processing/`.

**5.2 The refactor actions leave the core.**

- src: `syntax_tree/ast_refactor_actions.py` to the recipe `recipes/refactor_actions/`.
- test: `test/syntax_tree/test_ast_refactor_actions.py` to `test/unit/recipes/refactor_actions/`. Its import of
  `CPPPatternFactory` remains a known violation.
- remaining: the mirrors of `src/renaissance/recipes`, with `units = "packages"`.

**5.3 Close the core.** Moves nothing.

- src: removes `src/renaissance/syntax_tree/`.
- test: removes `test/syntax_tree/`.
- docs: removes the core API tables from [repository structure](repository-structure.md); the `__all__` lists are now the
  source of truth.
- remaining: gives the `layers` contract a container `renaissance.core` with `exhaustive = true`, so that a new core sub-package
  cannot escape the order.
- Checks: `git grep -E "renaissance\.(syntax_tree|utils|common)\b"` finds nothing; each core sub-package has its
  `protected` contract.

#### Phase 6: parser bindings

The tests of a binding move to its mirror under `test/unit/parser_bindings/`. Each step replaces the contract of the old
binding by one contract per new binding.

**6.1 The extractors leave the bindings.** They are recipes, so the bindings move without them.

- src: `integrations/python/ast/extractor.py` to `recipes/python_extractor/`, and `integrations/tree_sitter/extractor.py` to
  `recipes/code_graph_extractor/`.
- test: `test/extractors/` to `test/unit/recipes/python_extractor/` and `test/unit/recipes/code_graph_extractor/`.
- remaining: their imports of a binding are declared as dependencies of parser-specific recipes.

**6.2 The project scanners.**

- src: `project/` to `parser_bindings/project/`.
- test: `test/project/`.
- remaining: the mirrors of `src/renaissance/parser_bindings`, with `units = "packages"`.

**6.3 tree-sitter.**

- src: `integrations/tree_sitter/` to `parser_bindings/tree_sitter/`.
- test: `test/lst/`, except the tests of `clang_adapter`; `test/tree_sitter/`; `test/python/ast/test_python_lst_node.py`.
  `test/unit/parser_bindings/tree_sitter/` gets an `__init__.py`, unlike `test/tree_sitter/` today.
- Checks: `import tree_sitter` still finds the library in the tests.

**6.4 The Python parsers.**

- src: `integrations/python/ast/cst_node.py` to `parser_bindings/python/libcst/`, the rest to `parser_bindings/python/ast/`.
  The modules both use (`kinds.py`, `factory.py` and `util.py`) go to `python/ast/`, and `python/libcst/` imports them from
  there. These imports become visible as known violations, as
  [repository structure](repository-structure.md#imports-between-parser-bindings) anticipates; splitting them is an issue, not
  a step. `python/` is a grouping package: an `__init__.py` without imports.
- test: `test/python/ast/` to `python/ast/` and `python/libcst/`, by the binding each file tests.
- remaining: the grouping package is exempt from the docs mirrors.

**6.5 The clang parsers.**

- src: `integrations/clang/clang_json_ast_node.py` to `parser_bindings/clang/json_ast/`, the rest to
  `parser_bindings/clang/libclang/`. As in 6.4, the modules both use (`kinds.py`, `predicates.py`, `cpp_utils.py` and
  `c_pattern_factory.py`) go to `clang/libclang/`, and the imports of `clang/json_ast/` become known violations.
  `clang_adapter` keeps its known import of `tree_sitter`.
- test: `test/c_cpp/`, and the `clang_adapter` tests of `test/lst/`.
- Checks: `src/renaissance/integrations/`, `src/renaissance/project/`, `test/c_cpp/`, `test/python/`, `test/lst/`,
  `test/tree_sitter/`, `test/project/` and `test/extractors/` no longer exist; `git grep -E "renaissance\.(integrations|project)\b"`
  finds nothing; the `layers` contract has a container `renaissance.parser_bindings`, and each binding is independent.

#### Phase 7: recipes

**7.1 to 7.3 One package per recipe.** One step per recipe, in this order: `cleanup_refactoring`, `python_refactoring` and
`unit_to_pytest`.

- src: `recipes/<recipe>.py` to `recipes/<recipe>/`.
- test: `test/recipes/test_<recipe>.py` to `test/unit/recipes/<recipe>/`. `test_refactor_with_rewrite.py` goes to the recipe it
  exercises.

**7.4 The examples.**

- src: the modules of `src/rejuvenation/`, except `cli.py`, to `recipes/examples/`. This includes the examples that show how
  one parser represents code, such as `python_ast_example.py`; rewriting them as unit tests of their binding is not a move, so
  it is an issue.
- test: `test/examples/` to `test/unit/recipes/examples/`.

**7.5 The command line.**

- src: `src/rejuvenation/cli.py` to `recipes/cli/`; `src/rejuvenation/` no longer exists.
- remaining: `[project.scripts]` points `rejuvenate` to `renaissance.recipes.cli:refactor`; `rejuvenation` leaves
  `root_packages`.
- Checks: `uv run rejuvenate` starts as before; `git grep -E "\brejuvenation\."` finds nothing in `src/`,
  `test/` and `pyproject.toml`; the `layers` contract has a container `renaissance` with the layers `recipes`,
  `parser_bindings` and `core`, and `exhaustive = true`.

#### Phase 8: tests that are not unit tests

**8.1 The feature tests.**

- test: `features/` to `test/features/`.
- remaining: `testpaths`, `pythonpath` and `norecursedirs` of pytest; `src` and `extend-exclude` of Ruff; `include`, `exclude`
  and `extraPaths` of Pyright; `omit` of coverage; the commands in the CI workflows and in this page's gate.
  Import Linter now scans `test.features`, which it could not analyse at the root because of `targets/invalid.py`; the step
  excludes `test/features/targets/` from the scan, for example by removing its `__init__.py` files if no test imports them.
- Checks: `features/` no longer exists; the feature tests run and pass; the layering check reports `test.features`.

**8.2 The remaining test modules.**

- test: `test/search_strategies/` to `test/unit/shared/`. Its helper `python_type_and_value.py` has no users other than its
  own tests, which is recorded as a known violation.
  `test/conftest.py` stays.
- Checks: `test/` holds only `unit/`, `features/`, `tools/`, `test_data/`, `__init__.py` and `conftest.py`.

#### Phase 9: finishing

**9.1 One issue per known violation.** Creating issues changes a shared system, so it is done after the list is reviewed.
The list: the `ignore_imports` entries, the rows under [Known violations](repository-structure.md#known-violations), the
`known_issues` and the remaining `stale` entries in `[tool.check_references]`, the parser examples that should be unit tests of
their binding, and the unused helper `python_type_and_value.py`.

- remaining: each entry and each row links to its issue.

**9.2 Mark the structure as implemented.**

- docs: [repository structure](repository-structure.md) loses its *now in* columns and becomes *Implemented*, and no longer
  links to this page. This page and its entry in the `mkdocs.yml` nav are removed.
- remaining: the comment in `pyproject.toml` that says the module lists shrink as the migration proceeds is gone, and so are
  the references to the migration in the repository memory. The codespell ignore list applies to the code only again: it moves
  from `[tool.codespell]` in `pyproject.toml` back to the codespell step of the code quality workflow, so the documentation is
  checked without exceptions. It was shared only because this page quotes commands that contain the ignored words.
- Checks: every unit under `src/renaissance/` has its test directory and its pages;
  `git grep "repository-structure-migration"` finds nothing; `pyproject.toml` has no `[tool.codespell]`, and
  `uv run codespell ./docs` passes.

The pull request is then ready for review.

## Invariants / guarantees

- After each step, the gate passes and the step is committed and pushed.
- At every commit, each symbol is defined in exactly one place, and every referenced path exists.
- Every violation of the [repository structure](repository-structure.md) that remains after a step is recorded.

## Related features

## Related tests

## Related code

- `[tool.importlinter]` in `pyproject.toml`
- `[tool.check_layout]` in `pyproject.toml`

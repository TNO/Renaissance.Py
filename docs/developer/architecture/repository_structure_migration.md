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

Plan the moves that bring the repository from its current layout to the [repository structure](repository_structure.md),
in small steps that each leave the repository working.

## Scope

This page describes the order of the moves, what each step moves, and how to check that a step is done.
It does not describe the target structure; that is the [repository structure](repository_structure.md).
It does not fix violations of that structure: the migration moves code, and records each violation that remains.
The last step removes this page; git keeps its history.

## Definition

### Principles

- **Move, then fix.** A step either moves code or implements an issue that the migration depends on, never both.
  A step that moves code updates its importers. It does not change behaviour and introduces no new abstractions.
  A step that implements an issue does what the acceptance criteria of the issue require.
  A violation that a step makes visible is recorded: as an `ignore_imports` entry with its reason, or under
  [Known violations](repository_structure.md#known-violations). Once the migration is done, each known violation gets an issue.
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
  docstrings and comments, in feature files and in `docs/developer/feature_test_map/`. The guard rail of step 0.1 checks that
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
   [repository structure](repository_structure.md): the *now in* column, and the paths under Known violations.
   A page in `docs/developer/modules/` follows the [code module template](../../documentation_system/templates/code_module_template.md):
   its *Location*, *Validated by test modules* and *Related features* name the package, its test directory and its features.
   A page in `docs/developer/api/` renders the package with mkdocstrings, so the strict build fails when the package is missing.
   Existing pages that are organised by topic, such as `docs/developer/modules/matching.md`, stay; content that describes the
   moved package moves to its mirror page.
   Update every reference to a moved path: in the documentation, in `docs/developer/feature_test_map/`, and in docstrings,
   comments and feature files.
1. **remaining:** update `[tool.importlinter]`, `[tool.check_layout]`, `[tool.check_references]` and any other path in
   `pyproject.toml`, the CI workflows
   and the repository memory; run the gate; commit; push to `origin`.

### Gate

A step is done when each of the following commands exits with 0, run from the repository root in the activated virtual
environment.

- Tests: `python -m pytest -q -p no:cacheprovider`, with the same counts as after the previous step. After a step that
  implements an issue, every test that passed still passes or has its cases in a test that replaces it, and the counts change
  only as the step lists.
- Layering: `uv run lint-imports --no-cache`.
- Layout: `python -m tools.check_layout`.
- Names: `python -m tools.check_names`.
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
  it goes to `test/unit/shared/`, in step 3.2 if `test_c_match_finder.py` moves to the matcher, else in step 4.2.
- `test/utils/util_equivalence_classes.py`: used by three matcher tests in `test/python/ast/`. Step 3.2 decides whether they
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
- docs: `docs/developer/tools/check_references.md`, its entry in the tools index and in the `mkdocs.yml` nav. The paths that
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
- remaining: remove the two `ignore_imports` entries for the re-exports from the `layers` contract. `test.utils_for_tests`
  moves to the `core.match` layer: the re-exports hid its import of `PatternMatch`.
- Checks: `git grep -E "from renaissance\.syntax_tree import|from renaissance import syntax_tree"` finds nothing;
  `test_removed_legacy_api` still passes.

**0.3 Create the core.**

- src: `src/renaissance/core/__init__.py`, with a docstring only: the core exports nothing from its root.
- test: `test/unit/__init__.py` and `test/unit/core/__init__.py`.
- remaining: four mirrors of `src/renaissance/core` with `units = "packages"`: `test/unit/core/{path}/`,
  `docs/developer/modules/core/{path}.md`, `docs/developer/api/core/{path}.md` and `docs/user/core/{path}.md`.
- Checks: `python -m tools.check_layout` lists the four new mirrors, with no units yet.

#### Phase 1: `core.model` and `core.navigate`

The modules of this phase move to `core/model/`, their tests to `test/unit/core/model/`. Step 1.8 creates `core/navigate/`
and `test/unit/core/navigate/`. Step 1.9 creates `integrations/shared/`.

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
- test: `test/utils/test_text_utils.py` tests only `snake_case`, so its test class moves with it, to
  `test/recipes/test_python_refactoring.py`.

**1.4 The node utilities.**

- src: from `utils/ast_utils.py`, `traverse`, `display_context`, `process_node`, `preceding_sibling` and `next_sibling` to
  `core/model/node_utils.py`, and `match_props`, `match_children` and `format_node` to `core/model/for_bindings.py`.
  From `integrations/python/ast/util.py`, `to_str` to `recipes/python_refactoring.py` (internal). `convert` stays: a binding
  provides offsets into the UTF-8 encoded code, so turning a line and column into an offset is internal to the binding.
  `is_ancestor_of`, which is typed with the rewriter's `Rewritable`, moves to `syntax_tree/ast_rewriter.py`, its only user.
  `replace_dollar`, `use_dollar` and `detect_placeholder` are all that is left in `utils/ast_utils.py`.
- test: `test/utils/test_ast_utils.py`, which tests `is_ancestor_of`, becomes `test/syntax_tree/test_is_ancestor_of.py`.
  Its tests of `preceding_sibling` and `next_sibling` move to `test/unit/core/model/test_node_utils.py`.
- remaining: the known violation `renaissance.utils.ast_utils -> renaissance.syntax_tree.ast_rewriter` is removed, and that of
  the moved tests follows their new paths. A module expression cannot exclude a module, so the `protected` contract of
  `core.model` lists its modules, without `for_bindings`. That `ast_node` and `ast_shower` import the internal `process_node`
  and `display_context` is a known violation until step 1.5. The `protected` contract of `core.model.for_bindings`, which
  allows the core, `renaissance.integrations`, `renaissance.project` and their tests. The allowed importers follow the
  bindings as they move.

**1.8 The navigation, done before step 1.5.** Implements [issue 385](https://github.com/TNO/Renaissance.Py/issues/385): the
navigation protocols, and the package `core.navigate`, which imports nothing from the rest of the core and is the lowest core
layer, below `core.model`.

- src:
    - In `core/navigate/`, `protocols.py` defines the protocols `HasParent`, `HasChildren` and `NodeNavigateProtocol`, which
      combines them, and `navigate.py` the functions `is_ancestor_of`, `is_proper_ancestor_of`, `ancestors`,
      `proper_ancestors`, `nearest_ancestor`, `nearest_proper_ancestor`, `next_sibling` and `previous_sibling`. The functions
      compare nodes by identity.
    - `next_sibling` and `preceding_sibling` leave `core/model/node_utils.py`. `preceding_sibling` becomes `previous_sibling`,
      and so do the properties of `ASTNode`, `PythonCstNode`, `PythonRstNode` and the tree-sitter node, and their uses in
      `c_pattern_factory.py` and `ast_rewriter.py`.
    - `NodeProtocol` extends `NodeNavigateProtocol`, and the rewriter's `Rewritable` extends `HasParent`. `Siblings`
      implements neither.
    - The protocols type `parent` and `children` with `Self`, so `PythonPattern` and `PythonRstNode` do too, and create
      their children with `type(self)` instead of their class name.
    - `is_ancestor_of` leaves `syntax_tree/ast_rewriter.py`. Its two calls mean a proper ancestor, so they become
      `is_proper_ancestor_of`, and the rewriter behaves as before.
    - `ASTNode.get_ancestor(kind)` keeps its behaviour by delegating to `nearest_proper_ancestor`. `ASTNode.is_ancestor_of`,
      which compares by equality, and `is_descendant_of`, which calls it, are removed; their only user is a test.
- test:
    - `test/unit/core/navigate/` holds the unit tests that the acceptance criteria of issue 385 list. They use a test double
      of their own instead of a parser binding.
    - `test/syntax_tree/test_is_ancestor_of.py` and `test/unit/core/model/test_node_utils.py` test only functions that move
      to `core.navigate`, so their cases join these tests and the two files are removed.
    - `test_get_ancestor_finds_enclosing_function` in `test/python/ast/test_python_rst_node.py` calls
      `nearest_proper_ancestor` and loses its strict xfail marker.
    - The test of `is_ancestor_of` in `test/c_cpp/test_clang_ast_node.py` calls `is_proper_ancestor_of`, and the tests of the
      bindings use `previous_sibling`.
- docs:
    - The mirror pages of `core.navigate`: `docs/developer/modules/core/navigate.md`, `docs/developer/api/core/navigate.md`
      and `docs/user/core/navigate.md`. The user page of [navigation](../../user/features/navigation.md) links to the last
      one.
    - [Navigation of code](navigation.md) describes the protocols and the functions, and records the decisions of issue 385:
        - protocol names are verbs, after what they enable: match, rewrite and navigate, as in `NodeNavigateProtocol`;
        - `HasParent` and `HasChildren` are the basic protocols, and `NodeNavigateProtocol` combines them;
        - the protocols live in `core.navigate` with the functions that need them, as `Rewritable` lives with the rewriter.
          They cannot live in `core.model` while the functions are in `core.navigate`: `ASTNode` in `core.model` delegates
          to the functions, so the two packages would import each other;
        - an ancestor of a node includes the node itself, a proper ancestor excludes it, and nodes are compared by identity,
          never by equality;
        - `previous_sibling` and `next_sibling` are a symmetric pair, so `preceding_sibling` is not used;
        - `nearest_ancestor` and `nearest_proper_ancestor` take a predicate, so `core.navigate` needs no other protocol and
          does not decide how a kind matches;
        - `Siblings` keeps its name, with *slice* as a synonym for *range*;
        - `Siblings` implements neither `HasParent` nor `HasChildren`. Its `parent` is a node and never `None`. A slice is
          never its own ancestor, so the functions take a node, and code that needs the ancestors of `Siblings` calls them
          on `siblings.parent`. The children of the siblings have different parents, so they are not the children of any
          one node.
    - The [core model](../modules/core/model.md) page loses the sibling functions and calls `Siblings` a range, or slice.
    - [Repository structure](repository_structure.md): the core has six sub-packages, with `core.navigate` at the bottom;
      navigation leaves the responsibility of `core.model`; `core.navigate` gets its own table of symbols.
    - The sibling functions in [parser and AST modules](../modules/parser_and_ast.md).
- remaining: the `layers` contract gets the layer `renaissance.core.navigate : test.unit.core.navigate`, below `core.model`.
  The `protected` contract of `core.navigate`. In `[tool.check_layout]`, the mirror of the modules of `core/navigate/` in
  `test/unit/core/navigate/`, as for `core.model`. The removed test files leave the `layers` contract, and so do their
  `ignore_imports` entries. `node_utils` of `core.model` no longer has unit tests of its own, so it joins the exempt modules of
  its mirror.
- Checks: `git grep -wE "preceding_sibling|is_descendant_of" -- src test features` finds nothing; `is_ancestor_of` is defined
  only in `core/navigate/`; Pyright reports no new issues; the test counts change only by the tests that the step adds and
  removes, and by one xfailed test that now passes.

**1.9 The equality helpers leave the core, done before step 1.5.**

- src: `match_props` and `match_children` move from `core/model/for_bindings.py` to `integrations/shared/equal.py`, as
  `equal_in_properties` and `equal_in_children`: only parser bindings use them, and they need nothing from Renaissance.Py.
  `format_node` stays in the core, because it reads
  `DISPLAY_PARSER_KIND` of `core.model`, and `ASTNode` uses it; `for_bindings.py` becomes `format.py`. The four bindings that
  compare nodes import `equal`. `integrations/shared/` is the future `parser_bindings/shared/`, see
  [repository structure](repository_structure.md#bindings-share-helpers-in-parser_bindingsshared).
- test: `test/unit/integrations/shared/test_equal.py` tests `equal`, including the regression of the asymmetric
  `equal_in_children`; `format` has no unit tests of its own.
- docs: the [core model](../modules/core/model.md) page loses the equality helpers and names `format.py`.
- remaining: the `protected` contract of `core.model.for_bindings` becomes that of `core.model.format`, with the same allowed
  importers. `renaissance.integrations.shared` gets a `forbidden` contract, which forbids every other package of
  Renaissance.Py, and a `protected` contract, which allows `renaissance.integrations`, `renaissance.project` and their tests.
  `format` replaces `for_bindings` in the exempt modules of the mirror of `core.model`.
- Checks: `git grep -E "for_bindings|match_props|match_children" -- src test pyproject.toml` finds nothing;
  `equal_in_properties` and `equal_in_children` are defined only in `integrations/shared/equal.py`.

**1.5 The nodes.**

- src: `syntax_tree/ast_node.py`, `ast_factory.py`, `ast_finder.py` and `ast_shower.py`.
- test: `test/syntax_tree/test_node_finder.py`, `test_semantic_finder.py` and `test/c_cpp/test_ast_finder.py` test the model,
  so they become `test/unit/core/model/test_ast_finder___predicate.py`, `___semantic_kind.py` and `___parsed_c.py`.
  Their imports of a binding become known violations. `test_ast_factory.py`, `test_astshower.py`, `test_ast_references.py`
  and `test/python/ast/test_python_astshower.py` check what a binding provides, so they stay. `test/c_cpp/factories.py`
  goes to `test/unit/shared/`.
- remaining: the moved modules join the list of the `protected` contract of `core.model`. Its known violations by `ast_node`
  and `ast_shower` disappear, and `renaissance.syntax_tree.ast_node` leaves the allowed importers of
  `core.model.format`. `renaissance.utils`, which holds the placeholder helpers, moves to the layer of `core.pattern`.
  `test.unit.shared.factories` takes the place of `test.c_cpp.factories` in the contracts.
- Checks: `git grep -E "utils\.text_utils|syntax_tree\.(semantic_kind|node_protocol|text_segment|syntax_node|siblings)"` and
  `git grep -E "syntax_tree\.ast_(node|factory|finder|shower)"` find nothing outside the test input
  `features/targets/pyunit_test_example.py`; the model layer of the `layers` contract is `renaissance.core.model` and its
  tests.

**1.6 The ruff clean-up leaves the core.**

- src: `utils/ruff_utils.py` to `recipes/ruff_utils.py`. `run_ruff_import_cleanup` removes the imports that a recipe left
  unused and sorts the imports, so it is a recipe.
- test: `test/utils/test_ruff_utils.py` to `test/recipes/test_ruff_utils.py`.
- docs: the path of `ruff_utils.py` in [recipes](../modules/recipes.md).

**1.7 The libcst helpers go to the libcst binding.**

- src: `utils/cst_utils.py` to `integrations/python/ast/cst_utils.py`. Its helpers analyse the names in a libcst tree, which
  is the reference analysis that a binding provides; a recipe uses them as a step.
- test: `test/utils/test_cst_utils.py` to `test/python/ast/test_cst_utils.py`.
- docs: its paths in [recipes](../modules/recipes.md), the feature test map and type parameter modernization.

#### Phase 2: `core.pattern`

The modules of this phase move to `core/pattern/`, their tests to `test/unit/core/pattern/`.

**2.1 The pattern language.**

- src: `syntax_tree/pattern_kind.py`. `utils/ast_utils.py`, which holds `replace_dollar`, `use_dollar` and
  `detect_placeholder`, becomes `core/pattern/placeholders.py`, and `MATCH_ONE` and `MATCH_ALL` move there from
  `integrations/__init__.py`. They are part of the pattern language, so they are public. `pattern_kind` stays in
  `syntax_tree/match_finder.py`: only the matcher uses it.
- test: `test/syntax_tree/test_pattern_kind.py`.
- remaining: the known violation `renaissance.utils.ast_utils -> renaissance.integrations` disappears, because the markers are
  parser agnostic and now live in the core; remove its `ignore_imports` entry.
- Checks: `src/renaissance/utils/` no longer exists; `integrations/__init__.py` defines nothing.

#### Phase 3: `core.match`

The modules of this phase move to `core/match/`, their tests to `test/unit/core/match/`.

**3.1 The matcher.**

- src: `syntax_tree/match_finder.py`. `find_in_list` is public, because a binding uses it; `pattern_kind` is internal.
- test: `test/syntax_tree/test_match_finder.py`, `test_match_finder_multi_assignments.py`, `test_match_tree.py`,
  `test_match_dict.py` and `test_pattern_match.py`, as aspects of the tests of `match_finder`.
- remaining: the matcher tests of the bindings that import the internal `find_variants` or `variant_in_match_stmt` are known
  violations of the `protected` contract of `core.match`, until step 3.2.
- Checks: `git grep "syntax_tree.match_finder"` finds nothing outside the test input `features/targets/pyunit_test_example.py`.

**3.2 The matcher tests of the bindings.** Moves tests only.

- test: the matcher tests under `test/c_cpp/`, `test/python/ast/` and `test/lst/` move to `test/unit/core/match/` if they test
  the algorithm, and stay with their binding if they test how the binding presents its nodes to the matcher.
  This decides the users of `test/utils/util_equivalence_classes.py`, which moves to their `shared/` directory.
- remaining: the known violations of the `protected` contract of `core.match` disappear, or follow the tests that move.

#### Phase 4: `core.rewrite`

The modules of this phase move to `core/rewrite/`, their tests to `test/unit/core/rewrite/`.

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
- docs: removes the core API tables from [repository structure](repository_structure.md); the `__all__` lists are now the
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

**6.2 The project scanners and the shared helpers.**

- src: `project/` to `parser_bindings/project/`, and `integrations/shared/` to `parser_bindings/shared/`.
- test: `test/project/`, and `test/unit/integrations/shared/` to `test/unit/parser_bindings/shared/`.
- remaining: the mirrors of `src/renaissance/parser_bindings`, with `units = "packages"`. The contracts of `shared` follow it.

**6.3 tree-sitter.**

- src: `integrations/tree_sitter/` to `parser_bindings/tree_sitter/`.
- test: `test/lst/`, except the tests of `clang_adapter`; `test/python/ast/test_python_lst_node.py`.
- Checks: `import tree_sitter` still finds the library in the tests.

**6.4 The Python parsers.**

- src: `integrations/python/ast/cst_node.py` and `cst_utils.py` to `parser_bindings/python/libcst/`, the rest to
  `parser_bindings/python/ast/`.
  The modules both use (`kinds.py`, `factory.py` and `util.py`) go to `python/ast/`, and `python/libcst/` imports them from
  there. These imports become visible as known violations, as
  [repository structure](repository_structure.md#imports-between-parser-bindings) anticipates; splitting them is an issue, not
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
  `test/project/` and `test/extractors/` no longer exist; `git grep -E "renaissance\.(integrations|project)\b"`
  finds nothing; the `layers` contract has a container `renaissance.parser_bindings`, and each binding is independent.

#### Phase 7: recipes

**7.1 to 7.4 One package per recipe.** One step per recipe, in this order: `cleanup_refactoring`, `python_refactoring`,
`ruff_utils` and `unit_to_pytest`.

- src: `recipes/<recipe>.py` to `recipes/<recipe>/`.
- test: `test/recipes/test_<recipe>.py` to `test/unit/recipes/<recipe>/`. `test_refactor_with_rewrite.py` goes to the recipe it
  exercises.

**7.5 The examples.**

- src: the modules of `src/rejuvenation/`, except `cli.py`, to `recipes/examples/`. This includes the examples that show how
  one parser represents code, such as `cpp_clang_lst_example.py`; rewriting them as unit tests of their binding is not a move, so
  it is an issue.
- test: `test/examples/` to `test/unit/recipes/examples/`.

**7.6 The command line.**

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
The list: the `ignore_imports` entries, the rows under [Known violations](repository_structure.md#known-violations), the
`known_issues` and the remaining `stale` entries in `[tool.check_references]`, the parser examples that should be unit tests of
their binding, and the unused helper `python_type_and_value.py`.

- remaining: each entry and each row links to its issue.

**9.2 Mark the structure as implemented.**

- docs: [repository structure](repository_structure.md) loses its *now in* columns and becomes *Implemented*, and no longer
  links to this page. This page and its entry in the `mkdocs.yml` nav are removed.
- remaining: the comment in `pyproject.toml` that says the module lists shrink as the migration proceeds is gone, and so are
  the references to the migration in the repository memory. The codespell ignore list applies to the code only again: it moves
  from `[tool.codespell]` in `pyproject.toml` back to the codespell step of the code quality workflow, so the documentation is
  checked without exceptions. It was shared only because this page quotes commands that contain the ignored words.
- GitHub: the Renaissance.Py lint budget app is updated, because the file that holds the budgets was renamed from
  `lint-budget.json` to `lint_budget.json`.
- Checks: every unit under `src/renaissance/` has its test directory and its pages;
  `git grep "repository_structure_migration"` finds nothing; `pyproject.toml` has no `[tool.codespell]`, and
  `uv run codespell ./docs` passes.

The pull request is then ready for review.

## Invariants / guarantees

- After each step, the gate passes and the step is committed and pushed.
- At every commit, each symbol is defined in exactly one place, and every referenced path exists.
- Every violation of the [repository structure](repository_structure.md) that remains after a step is recorded.

## Related features

## Related tests

## Related code

- `[tool.importlinter]` in `pyproject.toml`
- `[tool.check_layout]` in `pyproject.toml`

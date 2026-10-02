# Refactoring recipes

{ #codemod-recipes }

**Stable ID:** `CODEMOD-RECIPES`

## Responsibility

Recipes are `PythonRefactoring` subclasses that inspect and rewrite one Python source file at a time, targeting
gaps that `ruff` either does not detect, only offers as a separate unsafe fix, or never finishes cleaning up. This
page covers `TypeVarCheck` and `TypeVarTupleCheck`, the recipes built for
[TypeVar modernization](../../user/features/typevar-modernization.md).

## Location

- `src/renaissance/recipes/type_var_check.py` - the `TypeVarCheck` pipeline itself (orchestration only).
- `src/renaissance/recipes/type_var_tuple_check.py`
- `src/renaissance/recipes/type_var_domain.py` - TypeVar/ParamSpec/TypeVarTuple domain model and safety
  analysis, shared between the two recipes above.
- `src/renaissance/recipes/step_runner.py` - `Step`/`run_steps`, the generic "run these independent fix actions
  in order, committing each one's owning recipe only if it fixed something" primitive that `TypeVarCheck.check()`
  and the CLI use.
- Base class: `src/renaissance/recipes/python_refactoring.py` - also owns two generic, cross-recipe helpers:
  `find_rst_node` (used by both recipes) and the module-level `narrowed_import_text` (used by `TypeVarCheck`'s
  import localization).
- Shared utilities: `src/renaissance/utils/unparse_utils.py` (splices the PEP 695 type-parameter bracket into a
  function's original source text),
  `src/renaissance/utils/import_resolution.py` (resolves `from X import Y` project-wide to the file it
  imports from - not TypeVar-specific, kept out of `type_var_domain.py` on purpose).

## Public entry points

- `TypeVarCheck.run()` / `TypeVarCheck.check()` — localizes cross-file type parameter imports, converts every
  declared type parameter to PEP 695 syntax (whether one function uses it or several), then removes any declaration left orphaned
  by outside means (e.g. a signature converted by hand or by `ruff`'s own `UP047` fix beforehand); commits changes
  to disk between phases (via `renaissance.recipes.step_runner.run_steps`, see below).
- `TypeVarCheck.localize_imported_typevars()`, `TypeVarCheck.convert_declared_typevars()`, and
  `TypeVarCheck.remove_orphaned_declarations()` — the three phases individually, each returning
  `{name: "fixed" | "unsafe"}`.
- `TypeVarTupleCheck.run()` / `TypeVarTupleCheck.fix_legacy_unpack_usage()` — rewrites every legacy `Unpack[T]`
  usage of a module-level `TypeVarTuple` to native `*T` syntax; the now-unused `Unpack` import is left for the
  CLI's `ruff` `F401` pass (see below). Gated by its own `_target_supports_pep646()` version check.
  `find_legacy_unpack_usage()` is detection-only, for any caller that just wants the names without touching the
  file; it and `fix_legacy_unpack_usage()` both build on `_find_unpack_occurrences`.
- Dispatched by name via `PythonRefactoring.process(class_name, file)`, which resolves `"TypeVarCheck"` to
  `renaissance.recipes.type_var_check` using `snake_case()`. Only the `refactor` subcommand of
  `src/rejuvenation/cli.py` uses this path, and it never sets `min_python`, `project_root` or
  `project_wide_imported_names`, so the version-gated rewrites are always reported `"unsafe"` there. The supported
  entry point is `migration-type-recipes.py`, which builds the recipes directly.
- `step_runner.run_steps(steps)` - `TypeVarCheck.check()` calls this internally with its own three phases;
  `migration-type-recipes.py` calls it twice per file (once for `TypeVarTupleCheck`'s single action, once for
  `TypeVarCheck`'s three phases - a fresh `TypeVarCheck` has to be constructed *after* the first call returns,
  since each recipe reads its file from disk only once, at construction). See the CLI's own docs.

## Internal structure

Both recipes operate on the plain `ast` module directly (`ast.walk`, `ast.iter_child_nodes`, `ast.unparse`) rather
than Renaissance's RstNode-tree traversal, because the cross-file phase already has to parse a second file from
disk with `ast.parse()`. Shared domain helpers (`find_type_param_declarations`, `type_param_constructor_name`,
plus the safety-analysis functions `is_safe_to_convert`/`is_safe_to_localize`) live in `type_var_domain.py`,
imported by both `type_var_check.py` and `type_var_tuple_check.py` - kept out of either recipe's own file so
domain modelling doesn't mix with pipeline orchestration.

`is_safe_to_convert`/`is_safe_to_localize` return `UnsafeReason | None` (`None` meaning safe), not a bare
`bool` - each of the eight `UnsafeReason` members (the two Python-version gates plus the six `__all__`/scope/
cross-project conditions across both functions) has a matching `UnsafeRule` (a short message plus a docs anchor
slug) in `UNSAFE_RULES`, and `doc_link(reason)` resolves one to the full URL under
[TypeVar modernization](../../user/features/typevar-modernization.md)'s Constraints section. `is_safe_to_convert`
additionally takes `project_wide_imported_names` (a `frozenset[str]`, defaulting to empty) - set on
`TypeVarCheck.project_wide_imported_names` by the CLI, via `renaissance.utils.import_resolution.
collect_project_imported_names` over every file it was given, before either `TypeVarCheck` phase that can
remove a declaration runs. Both `TypeVarCheck` and `TypeVarTupleCheck` record the reason behind each
`"unsafe"` name on their own instance attributes (see their own docs), and `migration-type-recipes.py`'s
report prints `UNSAFE_RULES[reason].message` and `doc_link(reason)`
next to each one - this is what makes a specific "unsafe" occurrence traceable to the exact documented rule that
caused it, rather than a generic status string. `TypeVarCheck.project_root` (a `Path | None`, falling back to the
file's own directory) is the directory absolute imports resolve from; the CLI sets it to the target directory, or
to the parent folder when given a single file.

`self.body` (top-level statements only) is not enough to rewrite a method nested in a class; `convert_declared_typevars`
locates the owning `PythonRstNode` for a nested function via `self.find_rst_node(function)` - a generic
`PythonRefactoring` base-class method (matching by node identity against the raw `ast.FunctionDef`/
`ast.AsyncFunctionDef` node), available to any future recipe needing the same lookup, not just this one. It skips
a function that already declares a matching PEP 695 `type_param` (rather than adding a duplicate) - the same
check that lets phase 2 absorb the "signature already converted, declaration left behind" case directly, without
needing phase 3 for it.

`convert_declared_typevars` calls `unparse_signature_only(function, original_text)` (from
`renaissance.utils.unparse_utils`) rather than `self.replace(unparse_node(function), ...)`: it splices only the
new `[T]`/`[**P]`/`[*Ts]` bracket into `function`'s *original* source text, right after its name, and leaves
everything else - parameter list, defaults, line breaks, return type, docstring, body, comments - untouched
(indentation aside: the header's continuation lines and the body are re-indented relative to `def`, see
`_renormalize_indent`), rather than regenerating anything from the AST, which used to reformat whatever it touched
(including collapsing a multi-line parameter list onto one line) and, since Python's `ast` module never records
comments at all, silently delete any comments inside the body. See
[Python AST known limitations](python-ast-known-limitations.md) item 1 for the full mechanism. It lives in a
shared utils module rather than in `type_var_check.py` itself, since any future recipe adding a type-params
bracket the same way needs it too.

`convert_declared_typevars` collects the functions it touches and queues exactly one `self.replace()` per
function, even when several type parameters apply to it: queuing one per name would target the same node twice
before a commit, which the rewriter rejects as a conflicting rewrite.

`functions_using_nodes` (`type_var_domain.py`) attributes a name's usage to the *outermost* function in a nesting
chain, never a nested closure that merely references it - a PEP 695 type parameter declared on an enclosing
function is already visible inside its nested closures the same way any other name in an enclosing scope is, so a
nested closure must never be treated as an independent user needing its own (shadowing) type parameter. Getting
this wrong used to queue a redundant edit for the nested closure alongside the outer function's edit - which,
combined with the rewrite dominance/suppression gap in
[Python AST known limitations](python-ast-known-limitations.md) item 2, corrupted the output outright. Confirmed
live against `starlette/starlette/authentication.py`'s `requires()` and its nested `*_wrapper` closures.

Neither recipe removes a now-unused import itself (e.g. `from typing import TypeVar` once nothing calls it) -
that used to be hand-rolled per recipe (`TypeVarCheck._remove_unused_constructor_imports`,
`TypeVarTupleCheck._has_other_unpack_subscript`), duplicating exactly what `ruff`'s `F401` rule already detects
generically. `migration-type-recipes.py` now runs `ruff check --fix --select F401` over every file it modified,
once, after both recipes have finished, unless `--no-ruff` is passed - see its own docs. `ruff` runs on the whole of
each modified file, so it removes every unused import there, not only the ones these recipes made unused.
`_localize_import` is a separate, still-hand-rolled concern that survives this: narrowing an import because a
name moved from *imported* to *locally declared* isn't "is this unused," so it isn't something `ruff` can do -
it still uses `narrowed_import_text` directly.

`remove_orphaned_declarations` detects a dead declaration without counting references: `all_refs_shadowed_by_pep695`
(in `type_var_domain.py`) walks the tree tracking whether the current position is "shadowed" (inside a function
whose `type_params` already declares the same name) and only reports a live use for a `Name` node reached while
*not* shadowed. This is what lets it recognize the state `ruff`'s `UP047` leaves behind — a signature already
rewritten to `def f[T](...)`, with the old `T = TypeVar("T")` still sitting in the module, which `ruff` documents
it will never remove itself.

Before rewriting anything, `convert_declared_typevars` calls `TypeVarCheck._target_supports_pep695()`, which
compares the recipe's `min_python` class attribute against `PEP_695_MINIMUM = (3, 12)`; `None` (unknown) never
passes. The tool doesn't detect the target's version: `migration-type-recipes.py` sets `min_python` from its
required `--py` flag, and tests set it after construction - the same pattern `in_memory` already uses on the base
class. `remove_orphaned_declarations` has no such check: removing a declaration that is already dead adds no
syntax.

`fix_legacy_unpack_usage` follows the identical pattern with its own threshold: `_target_supports_pep646()` /
`PEP_646_MINIMUM = (3, 11)`, `min_python` set the same way - see
[Python version gates](../../user/concepts/python-version-gates.md) for why this recipe's minimum is one version
below `TypeVarCheck`'s (PEP 646 landed a release before PEP 695), not raised to match it for consistency.

## Related features

- [TypeVar modernization](../../user/features/typevar-modernization.md)

## Related concepts

- [Python version gates](../../user/concepts/python-version-gates.md)

## Validated by test modules

- `test/recipes/test_type_var_check.py` - the end-to-end `run()`/`check()` path and the Python-version gate.
- `test/recipes/test_type_var_check_localize.py`
- `test/recipes/test_type_var_check_convert.py`
- `test/recipes/test_type_var_check_orphaned.py`
- `test/recipes/test_type_var_check_properties.py` - Hypothesis/hypothesmith crash-safety fuzzing of `check()`
  against arbitrary generated source (see [ADR 09](../architecture/adr/09_property_based_tests.md)).
- `test/recipes/test_type_var_tuple_check.py`
- `test/recipes/test_type_var_tuple_check_fix.py` - `fix_legacy_unpack_usage()`: the rewrite itself, its version
  gate, and that the `Unpack` import is left in place for `ruff` to clean up.
- `test/recipes/test_type_var_tuple_check_properties.py`
- `test/recipes/test_type_var_domain.py` - `is_safe_to_convert`/`is_safe_to_localize` in isolation, confirming
  that five of the `UnsafeReason` members (the `__all__`, outside-use, origin-export, generic-base and
  conditional-constructor conditions) are returned by their specific unsafe condition. The two version gates and
  `IMPORTED_ELSEWHERE_IN_PROJECT` are covered through the recipes and the CLI instead.
- `test/recipes/test_step_runner.py` - `Step`/`run_steps`: commit only when a step fixed something, results in step
  order.
- `test/recipes/test_python_refactoring.py` - `PythonRefactoring.find_rst_node` and `narrowed_import_text`.
- `test/recipes/conftest.py` - shared fixtures (`make_recipe`, `create_type_var_check`,
  `create_type_var_tuple_check`) used by the TypeVar test files above.
- `test/rejuvenation/test_migration_type_recipes.py` - the CLI: `--py` gating, the report and its documentation
  links, the `ruff` `F401` pass, exit codes, and the PEP 692 `**kwargs` case whose `Unpack` import must survive it.
- `test/utils/test_unparse_utils.py` - the bracket-splice mechanism itself (`unparse_signature_only` and its
  helpers), independent of the recipe.
- `test/utils/test_import_resolution.py` - `resolve_project_module`/`collect_project_imported_names` in
  isolation (absolute/relative import resolution, package `__init__.py` fallback, names read as attributes of
  an imported project module, stdlib imports correctly excluded).

## Extension points

- A new recipe is added as a new `PythonRefactoring` subclass in its own `snake_case`-named module under
  `src/renaissance/recipes/`; the CLI dispatch requires no separate registration.
- `build_type_param` (in `type_var_domain.py`) is the place to extend if a future PEP adds a new kind of
  type-parameter declaration.
- `PythonRefactoring.find_rst_node` and `renaissance.utils.unparse_utils.unparse_signature_only` are available to
  any new recipe that needs the same lookups - a future recipe doing signature-only `ast.unparse()` replacement
  doesn't need to reimplement it.
- `step_runner.Step`/`run_steps` are available to any new recipe (or CLI) that needs to sequence more than one
  independently-committable fix action.

## Non-goals

- `resolve_project_module` doesn't follow re-exports through an intermediate `__init__.py` or handle namespace
  packages (PEP 420); such imports are skipped by both the localization phase and the removal-safety check.
- A `from pkg.mod import *` is not expanded, so a name it pulls in is not detected by the removal-safety check.
- The names other files import from a module are computed once, before the first file is processed, so an origin
  whose importers all get localized in the same run is only converted by a second run.
- `localize_imported_typevars` queues one rewrite per localized name, so a single import statement that brings in
  two or more localizable names (`from .origin import T, U`) makes the commit fail with a conflicting-rewrite
  error. The CLI reports that file under `ERRORS` and leaves it unchanged; one import per name avoids it.
- Neither recipe detects the target's minimum Python version (e.g. from `requires-python`); it has to be given
  explicitly via `--py`.
- `TypeVarTupleCheck` only finds a **module-level** `TypeVarTuple` declaration in the same file, never one
  imported from another module - unlike `TypeVarCheck`, it has no cross-file localization phase of its own.
  When both recipes run together (`migration-type-recipes.py`), running `TypeVarTupleCheck` first lets it catch
  the common case before `TypeVarCheck` converts and removes the declaration out from under it, but a
  cross-file-imported `TypeVarTuple` used via `Unpack[T]` still needs a second CLI run to localize first, then
  fix - see [TypeVar modernization](../../user/features/typevar-modernization.md)'s Constraints section.

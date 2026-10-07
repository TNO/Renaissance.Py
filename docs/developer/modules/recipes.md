# Refactoring recipes

{ #codemod-recipes }

**Stable ID:** `CODEMOD-RECIPES`

## Responsibility

Recipes are `PythonRefactoring` subclasses that inspect and rewrite one Python source file at a time, targeting
gaps that `ruff` either does not detect, only offers as a separate unsafe fix, or never finishes cleaning up. This
page covers `TypeVarCheck`, the recipe built for
[TypeVar modernization](../../user/features/typevar-modernization.md). Recipes that were built and later
removed are listed in [Rejected recipes](rejected-recipes.md).

## Location

- `src/renaissance/recipes/type_var_check.py` - the `TypeVarCheck` pipeline itself (orchestration only).
- `src/renaissance/recipes/type_var_domain.py` - TypeVar/ParamSpec/TypeVarTuple domain model and safety
  analysis.
- `src/renaissance/recipes/step_runner.py` - `Step`/`run_steps`, the generic "run these independent fix actions
  in order, committing each one's owning recipe only if it fixed something" primitive that `TypeVarCheck.check()`
  uses.
- Base class: `src/renaissance/recipes/python_refactoring.py` - also owns two generic, cross-recipe helpers:
  `find_rst_node` (used by `TypeVarCheck`'s conversion) and the module-level `narrowed_import_text` (used by `TypeVarCheck`'s
  import localization).
- Shared utilities: `src/renaissance/utils/unparse_utils.py` (splices the PEP 695 type-parameter bracket into a
  function's original source text),
  `src/renaissance/utils/import_resolution.py` (resolves `from X import Y` project-wide to the file it
  imports from - not TypeVar-specific, kept out of `type_var_domain.py` on purpose).

## Public entry points

- `TypeVarCheck.run()` / `TypeVarCheck.check()` — localizes cross-file type parameter imports, adds PEP 695 type
  parameters to every function using a declared type parameter (whether one function uses it or several), then
  removes every declaration left orphaned, by that conversion or by outside means (e.g. a signature converted by
  hand or by `ruff`'s own `UP047` fix beforehand); commits changes to disk between phases (via
  `renaissance.recipes.step_runner.run_steps`, see below).
- `TypeVarCheck.localize_imported_typevars()`, `TypeVarCheck.convert_declared_typevars()` and
  `TypeVarCheck.remove_orphaned_declarations()` — the three phases individually, each returning
  `{name: "fixed" | "unsafe"}`. `convert_declared_typevars` only adds type parameters and
  `remove_orphaned_declarations` only removes declarations.
- Dispatched by name via `PythonRefactoring.process(class_name, file)`, which resolves `"TypeVarCheck"` to
  `renaissance.recipes.type_var_check` using `snake_case()`. Only the `refactor` subcommand of
  `src/rejuvenation/cli.py` uses this path, and it never sets `min_python`, `project_root` or
  `project_wide_imported_names`, so the version-gated rewrites are always reported `"unsafe"` there. The supported
  entry point is `migration-type-recipes.py`, which builds the recipe directly, sets those attributes and calls
  `check()` once per file.
- `step_runner.run_steps(steps)` - `TypeVarCheck.check()` calls this internally with its own three phases.

## Internal structure

The recipe operates on the plain `ast` module directly (`ast.walk`, `ast.iter_child_nodes`, `ast.unparse`) rather
than Renaissance's RstNode-tree traversal, because the cross-file phase already has to parse a second file from
disk with `ast.parse()`. Shared domain helpers (`find_type_param_declarations`, `type_param_constructor_name`,
plus the safety-analysis functions `is_safe_to_remove`/`is_safe_to_localize`) live in `type_var_domain.py`,
kept out of `type_var_check.py` so domain modelling doesn't mix with pipeline orchestration.

`is_safe_to_remove`/`is_safe_to_localize` return `UnsafeReason | None` (`None` meaning safe), not a bare
`bool` - each of the six `UnsafeReason` members (the Python-version gate plus the five `__all__`/scope/
cross-project conditions across both functions) has a matching `UnsafeRule` (a short message plus a docs anchor
slug) in `UNSAFE_RULES`, and `doc_link(reason)` resolves one to the full URL under
[TypeVar modernization](../../user/features/typevar-modernization.md)'s Constraints section. Adding `[T]` to a
function is always safe, so `is_safe_to_remove` only guards *removing* a declaration
(`remove_orphaned_declarations`); it never blocks `convert_declared_typevars`. It additionally takes
`project_wide_imported_names` (a `frozenset[str]`, defaulting to empty) - set on
`TypeVarCheck.project_wide_imported_names` by the CLI, via `renaissance.utils.import_resolution.
collect_project_imported_names` over every file it was given, before the `TypeVarCheck` phase that can remove a
declaration runs. `TypeVarCheck` records the reason behind each `"unsafe"` name on one instance
attribute per phase (see its own docs), and `migration-type-recipes.py`'s
report prints `UNSAFE_RULES[reason].message` and `doc_link(reason)`
next to each one - this is what makes a specific "unsafe" occurrence traceable to the exact documented rule that
caused it, rather than a generic status string. `TypeVarCheck.project_root` (a `Path | None`, falling back to the
file's own directory) is the directory absolute imports resolve from; the CLI sets it to the target directory, or
to the parent folder when given a single file.

`self.body` (top-level statements only) is not enough to rewrite a method nested in a class; `convert_declared_typevars`
locates the owning `PythonRstNode` for a nested function via `self.find_rst_node(function)` - a generic
`PythonRefactoring` base-class method (matching by node identity against the raw `ast.FunctionDef`/
`ast.AsyncFunctionDef` node), available to any future recipe needing the same lookup, not just this one. It skips
a function that already declares a matching PEP 695 `type_param` (rather than adding a duplicate), and every
method of a class generic over the name (`functions_in_generic_classes` in `type_var_domain.py`): adding `[T]`
there would shadow the class's own `T`. "Generic over a name" has one definition: `_declares_type_param` (the
class declares it, `class Box[T]:`) or `_inherits_type_param` (a base mentions it and the class doesn't declare its
own) - see [Generic classes](../../user/features/typevar-modernization.md#feature-typevar-modernization-generic-class).
A generic class at the origin of an import doesn't block localizing it: type checkers resolve the importing
file's copy of `T` in that file's own scopes.

`localize_imported_typevars` copies the origin's declaration exactly (`ast.unparse`) and imports from the origin
module every name its arguments use (`declaration_argument_names`, string forward references included). It
refuses to localize when one of those names can't be imported from the origin as the same object
(`DECLARATION_NAME_UNAVAILABLE`): the origin doesn't bind it at module level at runtime (only under
`if TYPE_CHECKING:`), or this file binds it to something else (`from_import_sources`).
A name that only such methods use is reported `"unsafe"` (`USED_IN_GENERIC_CLASS`). A name also used outside
functions (a `Generic[T]` base, a module-level alias) doesn't block converting the functions that use it:
`remove_orphaned_declarations` keeps the declaration as long as such a live reference remains.

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
before a commit, which the rewriter rejects as a conflicting rewrite. The type parameters are added in the order
their declarations appear in the file, so the same input always produces the same output.

`functions_using_nodes` (`type_var_domain.py`) attributes a name's usage to the *outermost* function in a nesting
chain, never a nested closure that merely references it - a PEP 695 type parameter declared on an enclosing
function is already visible inside its nested closures the same way any other name in an enclosing scope is, so a
nested closure must never be treated as an independent user needing its own (shadowing) type parameter. Getting
this wrong used to queue a redundant edit for the nested closure alongside the outer function's edit - which,
combined with the rewrite dominance/suppression gap in
[Python AST known limitations](python-ast-known-limitations.md) item 2, corrupted the output outright. Confirmed
live against `starlette/starlette/authentication.py`'s `requires()` and its nested `*_wrapper` closures.

The recipe doesn't remove a now-unused import itself (e.g. `from typing import TypeVar` once nothing calls it) -
that used to be hand-rolled (`TypeVarCheck._remove_unused_constructor_imports`), duplicating exactly what
`ruff`'s `F401` rule already detects generically. `migration-type-recipes.py` now runs
`ruff check --fix --select F401` over every file it modified, once, after the recipe has finished, unless
`--no-ruff` is passed - see its own docs. `ruff` runs on the whole of
each modified file, so it removes every unused import there, not only the ones these recipes made unused.
`_localize_import` is a separate, still-hand-rolled concern that survives this: narrowing an import because a
name moved from *imported* to *locally declared* isn't "is this unused," so it isn't something `ruff` can do -
it still uses `narrowed_import_text` directly.

`remove_orphaned_declarations` detects a dead declaration without counting references: `all_refs_shadowed_by_pep695`
(in `type_var_domain.py`) walks the tree tracking whether the current position is "shadowed" (inside a function,
or a function nested in one, whose `type_params` already declares the same name) and only reports a live use for
a `Name` node reached while *not* shadowed. `convert_declared_typevars` uses the same check to skip a name that
needs no conversion. This is what lets the recipe recognize both the state its own conversion leaves behind and
the one `ruff`'s `UP047` leaves — a signature already rewritten to `def f[T](...)`, with the old
`T = TypeVar("T")` still sitting in the module, which `ruff` documents it will never remove itself.

Before adding PEP 695 syntax, `convert_declared_typevars` calls `TypeVarCheck._target_supports_pep695()`, which
compares the recipe's `min_python` class attribute against `PEP_695_MINIMUM = (3, 12)`; `None` (unknown) never
passes. The tool doesn't detect the target's version: `migration-type-recipes.py` sets `min_python` from its
required `--py` flag, and tests set it after construction - the same pattern `in_memory` already uses on the base
class. `remove_orphaned_declarations` has no such check: removing a declaration that is already dead adds no
syntax.

## Related features

- [TypeVar modernization](../../user/features/typevar-modernization.md)

## Related concepts

- [Python version gates](../../user/concepts/python-version-gates.md)

## Validated by test modules

- `test/recipes/test_type_var_check.py` - the end-to-end `run()`/`check()` path, including a target below the
  Python-version gate.
- `test/recipes/test_type_var_check_localize.py`
- `test/recipes/test_type_var_check_convert.py`
- `test/recipes/test_type_var_check_orphaned.py`
- `test/recipes/test_type_var_check_properties.py` - Hypothesis/hypothesmith crash-safety fuzzing of `check()`
  against arbitrary generated source (see [ADR 09](../architecture/adr/09_property_based_tests.md)).
- `test/recipes/test_type_var_domain.py` - `is_safe_to_remove`/`is_safe_to_localize` in isolation, confirming
  that three of the `UnsafeReason` members (the `__all__`, imported-elsewhere and conditional-constructor
  conditions) are returned by their specific unsafe condition. The version gate, `USED_IN_GENERIC_CLASS` and
  `DECLARATION_NAME_UNAVAILABLE` are covered through the recipe instead.
- `test/recipes/test_step_runner.py` - `Step`/`run_steps`: commit only when a step fixed something, results in step
  order.
- `test/recipes/test_python_refactoring.py` - `PythonRefactoring.find_rst_node` and `narrowed_import_text`.
- `test/recipes/conftest.py` - shared fixtures (`make_recipe`, `create_type_var_check`) used by the TypeVar test
  files above.
- `test/rejuvenation/test_migration_type_recipes.py` - the CLI: `--py` gating, the report and its documentation
  links, the `ruff` `F401` pass and exit codes.
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

## Fixes to be made/ Non-Goals

- `resolve_project_module` doesn't follow re-exports through an intermediate `__init__.py` or handle namespace
  packages (PEP 420); such imports are skipped by both the localization phase and the removal-safety check.
- A `from pkg.mod import *` is not expanded, so a name it pulls in is not detected by the removal-safety check.
- `localize_imported_typevars` skips an aliased import (`from .origin import T as U`) without reporting it.
- The names other files import from a module are computed once, before the first file is processed, so an origin
  whose importers all get localized in the same run is only converted by a second run.
- `localize_imported_typevars` queues one rewrite per localized name, so a single import statement that brings in
  two or more localizable names (`from .origin import T, U`) makes the commit fail with a conflicting-rewrite
  error. The CLI reports that file under `ERRORS` and leaves it unchanged; one import per name avoids it.
  Tracked by the `xfail` test `test_localizes_two_names_from_one_import_statement` in
  `test/recipes/test_type_var_check_localize.py`.
- The recipe doesn't detect the target's minimum Python version (e.g. from `requires-python`); it has to be given
  explicitly via `--py`.
- Rewriting legacy `Unpack[Ts]` usages to native `*Ts` syntax is left to `ruff`'s `UP044` rule - see
  [Rejected recipes](rejected-recipes.md).

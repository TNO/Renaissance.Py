# Refactoring recipes

{ #codemod-recipes }

**Stable ID:** `CODEMOD-RECIPES`

## Responsibility

Recipes are `PythonRefactoring` subclasses that inspect and rewrite one Python source file at a time, targeting
gaps that `ruff` either does not detect, only offers as a separate unsafe fix, or never finishes cleaning up. This
page covers `TypeVarCheck` and `TypeVarTupleCheck`, the recipes built for
[TypeVar modernization](../../user/features/typevar-modernization.md).

## Location

- `src/renaissance/refactoring/type_var_check.py` - the `TypeVarCheck` pipeline itself (orchestration only).
- `src/renaissance/refactoring/type_var_tuple_check.py`
- `src/renaissance/refactoring/type_var_domain.py` - TypeVar/ParamSpec/TypeVarTuple domain model and safety
  analysis, shared between the two recipes above.
- Base class: `src/renaissance/refactoring/python_refactoring.py` - also owns two generic, cross-recipe
  primitives that `TypeVarCheck` uses: `find_rst_node` and `remove_import_alias`.
- Shared utilities: `src/renaissance/utils/python_version.py` (minimum-supported-Python-version detection),
  `src/renaissance/utils/unparse_utils.py` (the `ast.unparse()` docstring-indent workaround).

## Public entry points

- `TypeVarCheck.run()` / `TypeVarCheck.check()` — localizes cross-file type parameter imports, converts every
  declared type parameter (single- or multi-scope) to PEP 695 syntax, then removes any declaration left orphaned
  by outside means (e.g. a signature converted by hand or by `ruff`'s own `UP047` fix beforehand); commits changes
  to disk between phases. One CLI invocation runs all three - no separate `ruff` step needed.
- `TypeVarCheck.localize_imported_typevars()`, `TypeVarCheck.convert_declared_typevars()`, and
  `TypeVarCheck.remove_orphaned_declarations()` — the three phases individually, each returning
  `{name: "fixed" | "unsafe"}`.
- `TypeVarTupleCheck.run()` / `TypeVarTupleCheck.fix_legacy_unpack_usage()` — rewrites every legacy `Unpack[T]`
  usage of a module-level `TypeVarTuple` to native `*T` syntax, dropping the now-unused `Unpack` import unless
  the file separately needs it (e.g. PEP 692 `**kwargs: Unpack[SomeTypedDict]`); gated by its own
  `target_supports_pep646` version check. `find_legacy_unpack_usage()` still exists, detection-only, for any
  caller that just wants the names without touching the file - it's what `fix_legacy_unpack_usage()` is built on
  top of, not a separate code path.
- Dispatched from the CLI via `PythonRefactoring.process(class_name, file)`, which resolves `"TypeVarCheck"` to
  `renaissance.refactoring.type_var_check` using `snake_case()`.

## Internal structure

Both recipes operate on the plain `ast` module directly (`ast.walk`, `ast.iter_child_nodes`, `ast.unparse`) rather
than Renaissance's RstNode-tree traversal, because the cross-file phase already has to parse a second file from
disk with `ast.parse()`. Shared domain helpers (`find_type_param_declarations`, `type_param_constructor_name`,
plus the safety-analysis functions `is_safe_to_convert`/`is_safe_to_localize`) live in `type_var_domain.py`,
imported by both `type_var_check.py` and `type_var_tuple_check.py` - kept out of either recipe's own file so
domain modelling doesn't mix with pipeline orchestration.

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
everything else - parameter list, defaults, line breaks, return type, docstring, body, comments - byte-for-byte
untouched, rather than regenerating anything from the AST, which used to reformat whatever it touched (including
collapsing a multi-line parameter list onto one line) and, since Python's `ast` module never records comments at
all, silently delete any comments inside the body. See python-ast-known-limitations.md item 4 for the full
mechanism. It lives in a shared utils module rather than in `type_var_check.py` itself, since any future recipe
adding a type-params bracket the same way needs it too.

`functions_using_nodes` (`type_var_domain.py`) attributes a name's usage to the *outermost* function in a nesting
chain, never a nested closure that merely references it - a PEP 695 type parameter declared on an enclosing
function is already visible inside its nested closures the same way any other name in an enclosing scope is, so a
nested closure must never be treated as an independent user needing its own (shadowing) type parameter. Getting
this wrong used to queue a redundant edit for the nested closure alongside the outer function's edit - which,
combined with the rewrite dominance/suppression gap in python-ast-known-limitations.md item 5, corrupted the
output outright. Confirmed live against `starlette/starlette/authentication.py`'s `requires()` and its nested
`*_wrapper` closures.

Removing a now-unused import (e.g. `from typing import TypeVar` once nothing calls it) uses
`self.remove_import_alias(name)`, another generic `PythonRefactoring` base-class method - it only edits the import
statement; deciding *whether* a name is still needed stays each recipe's own responsibility
(`TypeVarCheck._remove_constructor_import_if_unused` walks the tree for remaining `Call` references,
`_localize_import` reuses the same alias-filtering primitive via `narrowed_import_text`).

`remove_orphaned_declarations` detects a dead declaration without counting references: `_all_refs_shadowed_by_pep695`
(in `type_var_domain.py`) walks the tree tracking whether the current position is "shadowed" (inside a function
whose `type_params` already declares the same name) and only reports a live use for a `Name` node reached while
*not* shadowed. This is what lets it recognize the state `ruff`'s `UP047` leaves behind — a signature already
rewritten to `def f[T](...)`, with the old `T = TypeVar("T")` still sitting in the module, which `ruff` documents
it will never remove itself.

Before rewriting anything, `convert_declared_typevars` calls `TypeVarCheck._target_supports_pep695()`, which in turn
calls `target_supports_pep695(file_path)` (a standalone function in `type_var_check.py`, so it can be tested without
constructing a recipe). That function only compares `renaissance.utils.python_version.minimum_python_version(file_path)`
against `PEP_695_MINIMUM = (3, 12)` - the filesystem lookup (nearest `pyproject.toml`, `requires-python` parsing)
lives in that shared utility module, not here, since any future recipe whose rewrite depends on a minimum Python
version needs the same detection, not just this one. `TypeVarCheck.min_python_override` is a class attribute a test
can set after construction to bypass the filesystem lookup entirely - the same pattern `in_memory` already uses on
the base class.

`fix_legacy_unpack_usage` follows the identical pattern with its own threshold: `_target_supports_pep646()` /
`target_supports_pep646(file_path)` / `PEP_646_MINIMUM = (3, 11)`, `min_python_override` set the same way - see
[Python version gates](../../user/concepts/python-version-gates.md) for why this recipe's minimum is one version
below `TypeVarCheck`'s (PEP 646 landed a release before PEP 695), not raised to match it for consistency.

## Related features

- [TypeVar modernization](../../user/features/typevar-modernization.md)

## Related concepts

- [Type parameter scope](../../user/concepts/type-parameter-scope.md)
- [Python version gates](../../user/concepts/python-version-gates.md)

## Validated by test modules

- `test/refactoring/test_type_var_check.py` - multi-scope detection, the end-to-end `run()`/`check()` path, and
  the Python-version gate.
- `test/refactoring/test_type_var_check_localize.py`
- `test/refactoring/test_type_var_check_convert.py`
- `test/refactoring/test_type_var_check_orphaned.py`
- `test/refactoring/test_type_var_check_properties.py`
- `test/refactoring/test_type_var_tuple_check.py`
- `test/recipes/test_type_var_tuple_check_fix.py` - `fix_legacy_unpack_usage()`: the rewrite itself, its version
  gate, and the `Unpack` import cleanup (including the PEP 692 `**kwargs` case it must leave alone).
- `test/refactoring/test_type_var_tuple_check_properties.py`
- `test/refactoring/conftest.py` - shared fixtures (`make_recipe`, `create_type_var_check`,
  `create_type_var_tuple_check`) used across the files above and by other recipes' tests.
- `test/utils/test_unparse_utils.py` - the bracket-splice mechanism itself (`unparse_signature_only` and its
  helpers), independent of the recipe.

## Extension points

- A new recipe is added as a new `PythonRefactoring` subclass in its own `snake_case`-named module under
  `src/renaissance/refactoring/`; the CLI dispatch requires no separate registration.
- `_build_type_param` (in `type_var_domain.py`) is the place to extend if a future PEP adds a new kind of
  type-parameter declaration.
- `PythonRefactoring.find_rst_node`/`remove_import_alias` and `renaissance.utils.unparse_utils.unparse_signature_only`
  are available to any new recipe that needs the same lookups - a future recipe doing signature-only
  `ast.unparse()` replacement or import cleanup doesn't need to reimplement them.

## Non-goals

- `find_multi_scope_typevars()` is purely informational (reports names shared across 2+ functions) - it does not
  decide safety or apply a fix; both single- and multi-scope names are converted the same way by
  `convert_declared_typevars()`, which decides safety via `is_safe_to_convert`.
- Neither recipe resolves package-qualified or dotted-module imports for the cross-file phase.
- The Python-version gates (`target_supports_pep695` and `target_supports_pep646`, both backed by
  `renaissance.utils.python_version`) only recognise `requires-python` specifiers matching a known, hardcoded
  list of versions (3.8-3.14) - an exotic specifier that matches none of them is treated as unknown, the same as
  a missing one, and blocks the rewrite.
- `TypeVarTupleCheck` only finds a **module-level** `TypeVarTuple` declaration in the same file, never one
  imported from a sibling module - unlike `TypeVarCheck`, it has no cross-file localization phase of its own.
  When both recipes run together (`migration-type-recipes.py`), running `TypeVarTupleCheck` first lets it catch
  the common case before `TypeVarCheck` converts and removes the declaration out from under it, but a
  cross-file-imported `TypeVarTuple` used via `Unpack[T]` still needs a second CLI run to localize first, then
  fix - see [TypeVar modernization](../../user/features/typevar-modernization.md)'s Constraints section.

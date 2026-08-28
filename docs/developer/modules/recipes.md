# Refactoring recipes

{ #codemod-recipes }

**Stable ID:** `CODEMOD-RECIPES`

## Responsibility

Recipes are `PythonRefactoring` subclasses that inspect and rewrite one Python source file at a time, targeting
gaps that `ruff` either does not detect, only offers as a separate unsafe fix, or never finishes cleaning up. This
page covers `TypeVarCheck` and `TypeVarTupleCheck`, the recipes built for
[TypeVar modernization](../../user/features/typevar-modernization.md).

## Location

- `src/renaissance/refactoring/type_var_check.py`
- `src/renaissance/refactoring/type_var_tuple_check.py`
- Base class: `src/renaissance/refactoring/python_refactoring.py`

## Public entry points

- `TypeVarCheck.run()` / `TypeVarCheck.check()` — localizes cross-file type parameter imports, converts every
  declared type parameter (single- or multi-scope) to PEP 695 syntax, then removes any declaration left orphaned
  by outside means (e.g. a signature converted by hand or by `ruff`'s own `UP047` fix beforehand); commits changes
  to disk between phases. One CLI invocation runs all three - no separate `ruff` step needed.
- `TypeVarCheck.localize_imported_typevars()`, `TypeVarCheck.convert_declared_typevars()`, and
  `TypeVarCheck.remove_orphaned_declarations()` — the three phases individually, each returning
  `{name: "fixed" | "unsafe"}`.
- `TypeVarTupleCheck.run()` — detects legacy `Unpack[Ts]` usage for a `TypeVarTuple` declared in the same file
  (report-only, no fix yet).
- Dispatched from the CLI via `PythonRefactoring.process(class_name, file)`, which resolves `"TypeVarCheck"` to
  `renaissance.refactoring.type_var_check` using `snake_case()`.

## Internal structure

Both recipes operate on the plain `ast` module directly (`ast.walk`, `ast.iter_child_nodes`, `ast.unparse`) rather
than Renaissance's RstNode-tree traversal, because the cross-file phase already has to parse a second file from
disk with `ast.parse()`. Shared helpers (`find_type_param_declarations`, `type_param_constructor_name`) live in
`type_var_check.py` and are imported by `type_var_tuple_check.py` to avoid duplicating the declaration-scanning
logic.

`self.body` (top-level statements only) is not enough to rewrite a method nested in a class; `convert_declared_typevars`
locates the owning `PythonRstNode` for a nested function via `self.root.process(...)`, matching by node identity
against the raw `ast.FunctionDef`/`ast.AsyncFunctionDef` node. It skips a function that already declares a matching
PEP 695 `type_param` (rather than adding a duplicate) - the same check that lets phase 2 absorb the "signature
already converted, declaration left behind" case directly, without needing phase 3 for it.

`remove_orphaned_declarations` detects a dead declaration without counting references: `_all_refs_shadowed_by_pep695`
walks the tree tracking whether the current position is "shadowed" (inside a function whose `type_params` already
declares the same name) and only reports a live use for a `Name` node reached while *not* shadowed. This is what
lets it recognize the state `ruff`'s `UP047` leaves behind — a signature already rewritten to `def f[T](...)`, with
the old `T = TypeVar("T")` still sitting in the module, which `ruff` documents it will never remove itself.

## Related features

- [TypeVar modernization](../../user/features/typevar-modernization.md)

## Related concepts

- [Type parameter scope](../../user/concepts/type-parameter-scope.md)

## Validated by test modules

- `test/refactoring/test_type_var_check.py`
- `test/refactoring/test_type_var_check_properties.py`
- `test/refactoring/test_type_var_tuple_check.py`
- `test/refactoring/test_type_var_tuple_check_properties.py`

## Extension points

- A new recipe is added as a new `PythonRefactoring` subclass in its own `snake_case`-named module under
  `src/renaissance/refactoring/`; the CLI dispatch requires no separate registration.
- `_build_type_param` is the place to extend if a future PEP adds a new kind of type-parameter declaration.

## Non-goals

- `find_multi_scope_typevars()` is purely informational (reports names shared across 2+ functions) - it does not
  decide safety or apply a fix; both single- and multi-scope names are converted the same way by
  `convert_declared_typevars()`, which decides safety via `is_safe_to_convert`.
- Neither recipe resolves package-qualified or dotted-module imports for the cross-file phase.
- `convert_declared_typevars()` does not check the target codebase's minimum supported Python version. PEP 695
  syntax requires 3.12+; nothing in `type_var_check.py` reads `requires-python` or otherwise gates the rewrite,
  unlike `ruff`'s `UP047` - see the Constraints section of
  [TypeVar modernization](../../user/features/typevar-modernization.md).

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
- `TypeVarTupleCheck.run()` — detects legacy `Unpack[Ts]` usage for a `TypeVarTuple` declared in the same file
  (report-only, no fix yet).
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

`convert_declared_typevars` calls `unparse_node(function)` (from `renaissance.utils.unparse_utils`) rather than
`ast.unparse(function)` directly. It's the same output except when `function` has a multi-line docstring:
`normalize_docstring_indent` first resets the docstring's continuation lines to a single canonical indent
(preserving their indentation *relative* to each other) before unparsing, working around a shared rewrite-mechanism
bug that would otherwise double-indent those lines - see python-ast-known-limitations.md item 4 for the full
mechanism. The workaround lives in a shared utils module rather than in `type_var_check.py` itself, since any
future recipe doing the same kind of whole-node `ast.unparse()` replacement needs it too.

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

## Related features

- [TypeVar modernization](../../user/features/typevar-modernization.md)

## Related concepts

- [Type parameter scope](../../user/concepts/type-parameter-scope.md)

## Validated by test modules

- `test/refactoring/test_type_var_check.py` - multi-scope detection, the end-to-end `run()`/`check()` path, and
  the Python-version gate.
- `test/refactoring/test_type_var_check_localize.py`
- `test/refactoring/test_type_var_check_convert.py`
- `test/refactoring/test_type_var_check_orphaned.py`
- `test/refactoring/test_type_var_check_properties.py`
- `test/refactoring/test_type_var_tuple_check.py`
- `test/refactoring/test_type_var_tuple_check_properties.py`
- `test/refactoring/conftest.py` - shared fixtures (`make_recipe`, `create_type_var_check`) used across the files
  above and by other recipes' tests.

## Extension points

- A new recipe is added as a new `PythonRefactoring` subclass in its own `snake_case`-named module under
  `src/renaissance/refactoring/`; the CLI dispatch requires no separate registration.
- `_build_type_param` (in `type_var_domain.py`) is the place to extend if a future PEP adds a new kind of
  type-parameter declaration.
- `PythonRefactoring.find_rst_node`/`remove_import_alias` and `renaissance.utils.unparse_utils.unparse_node` are
  available to any new recipe that needs the same lookups - a future recipe doing whole-node `ast.unparse()`
  replacement or import cleanup doesn't need to reimplement them.

## Non-goals

- `find_multi_scope_typevars()` is purely informational (reports names shared across 2+ functions) - it does not
  decide safety or apply a fix; both single- and multi-scope names are converted the same way by
  `convert_declared_typevars()`, which decides safety via `is_safe_to_convert`.
- Neither recipe resolves package-qualified or dotted-module imports for the cross-file phase.
- The Python-version gate (`target_supports_pep695`, backed by `renaissance.utils.python_version`) only recognises
  `requires-python` specifiers matching a known, hardcoded list of versions (3.8-3.14) - an exotic specifier that
  matches none of them is treated as unknown, the same as a missing one, and blocks the PEP 695 rewrite.

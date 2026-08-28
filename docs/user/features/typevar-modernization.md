# TypeVar modernization

{ #feature-typevar-modernization }

**Stable ID:** `FEATURE-TYPEVAR-MODERNIZATION`

## User-facing summary

Modernizes legacy `TypeVar`/`ParamSpec`/`TypeVarTuple` usage in a Python file end to end, in one command —
covering both what `ruff`'s `UP047` rule only offers as a separate, unsafe fix and a gap it doesn't detect or
clean up at all:

1. **Cross-file import localization.** A type parameter imported from a sibling module
   (`from other_module import T`) is invisible to `ruff`'s `UP047` rule, which only looks at declarations in the
   same file. Where safe, the recipe rewrites the import into an equivalent local declaration.
2. **Conversion to PEP 695 syntax.** Every declared `TypeVar`/`ParamSpec`/`TypeVarTuple` is rewritten to
   [PEP 695](https://peps.python.org/pep-0695/) generic syntax (`def f[T](...)`) across every function that uses
   it — whether it's used by one function (the same rewrite `ruff` offers, but only via `--unsafe-fixes`) or
   shared across several (see [Type parameter scope](../concepts/type-parameter-scope.md); `ruff` can't safely do
   this at all, since converting one function at a time never lets it confirm every use site is covered). The
   now-redundant module-level declaration is removed as part of the same pass.
3. **Orphaned declaration cleanup.** A defensive final pass for declarations left dead by outside means — e.g. a
   signature already converted to PEP 695 syntax by hand, or by running `ruff` before this recipe. `ruff`'s
   `UP047`, by its own documentation, never removes the module-level `T = TypeVar("T")` it makes redundant, in
   any case. Once every remaining reference to a declared name is shadowed by a same-named PEP 695 type parameter
   (or there's no reference left at all), the recipe removes the declaration and, if now unused, its import.

## Inputs

A single Python source file, passed by path.

## Outputs / effects

- The file is rewritten in place for every change classified as safe.
- A result summary is returned: `{"cross_file": {...}, "converted": {...}, "orphaned": {...}}`, each mapping
  `name -> "fixed" | "unsafe"`.
- A `from typing import ...` (or equivalent) name is dropped once a conversion makes it redundant, as long as no
  other declaration in the file still needs it.

## Constraints

- **Requires Python 3.12+ on the target codebase.** [PEP 695](https://peps.python.org/pep-0695/) generic syntax
  (`def f[T](...)`) did not exist before Python 3.12 (released October 2023) — running this recipe against a
  codebase that must keep supporting an older interpreter produces a hard `SyntaxError` there. This recipe is
  currently scoped to 3.12+ targets only, by design: support for gating or targeting older Python versions is
  intentionally deferred, not yet built. The recipe does not read the target project's `requires-python` (or any
  other version marker) and does not check the interpreter it runs under either — unlike `ruff`, which skips
  `UP047` unless the target's declared minimum version is 3.12+. Confirm the target project's minimum supported
  Python version is 3.12+ before running it.
- The cross-file phase only resolves simple, same-directory sibling imports (`from module_name import T`);
  dotted/package imports are out of scope.
- A candidate is left unconverted (`"unsafe"`) if the name is re-exported via `__all__`, or referenced outside a
  function body — for example as a `Generic[...]` base — see
  [Type parameter scope](../concepts/type-parameter-scope.md).
- Supports `TypeVar` (including `bound=` and constraint forms), `ParamSpec`, and `TypeVarTuple`.

## Related concepts

- [Type parameter scope](../concepts/type-parameter-scope.md)

## Verified by test modules

- `test/refactoring/test_type_var_check.py`
- `test/refactoring/test_type_var_check_properties.py`
- `test/refactoring/test_type_var_tuple_check.py`
- `test/refactoring/test_type_var_tuple_check_properties.py`

## Implemented by code modules

- [Refactoring recipes](../../developer/modules/recipes.md)

## API entry points

```shell
rejuvenate refactor TypeVarCheck <file>
```

Equivalently, `PythonRefactoring.process("TypeVarCheck", file)`.

## Change considerations

- Supporting a future type-parameter-declaring construct means extending `_is_type_param_call` and
  `_build_type_param` in `type_var_check.py` together.
- The cross-file phase only resolves same-directory imports; supporting package-qualified imports would need
  `_resolve_sibling_module` to handle dotted module names.
- No Python-version gate exists yet (see Constraints above); the recipe intentionally targets 3.12+ codebases
  only for now. Supporting older targets later would mean resolving the target project's `requires-python` (or
  an explicit CLI flag) before `convert_declared_typevars` runs, and treating a too-low minimum version the same
  way an unsafe candidate is treated today — reported, not converted.

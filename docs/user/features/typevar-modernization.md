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

- **PEP 695 conversion only applies when the target codebase declares Python 3.12+.**
  [PEP 695](https://peps.python.org/pep-0695/) generic syntax (`def f[T](...)`) did not exist before Python 3.12
  (released October 2023). Before rewriting, the recipe finds the nearest `pyproject.toml` above the file being
  refactored and checks its `requires-python`; if the lowest version that specifier allows is below 3.12 - or no
  `pyproject.toml` is found, or `requires-python` is missing or unparsable - every candidate is reported
  `"unsafe"` and left untouched, the same conservative treatment as any other unsafe candidate. Cross-file
  localization (phase 1) is unaffected by this check and always runs, since it never introduces PEP 695 syntax.
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
  `_build_type_param` in `type_var_domain.py` together.
- The cross-file phase only resolves same-directory imports; supporting package-qualified imports would need
  `_resolve_sibling_module` (also in `type_var_domain.py`) to handle dotted module names.
- The version gate (see Constraints above) only recognises versions in a known list (3.8 through 3.14, see
  `KNOWN_PYTHON_VERSIONS` in `renaissance/utils/python_version.py`); extending it to a new Python release means
  adding that release to the list.
- There's no CLI flag to override the detected minimum version; `TypeVarCheck.min_python_override` exists for
  tests but isn't exposed on the command line.
- **Resolved: whole-function replacement used to reformat more than the signature, and delete comments.**
  `convert_declared_typevars` only ever *adds* a `type_params` entry, but used to replace the *entire* function via
  `self.replace(unparse_node(function), ...)`, so `ast.unparse()` regenerated every line of the body in its own
  style - confirmed live against `sqlalchemy/lib/sqlalchemy/sql/elements.py` (reformatting) and
  `starlette/starlette/concurrency.py` (a body comment deleted outright, since Python's `ast` module never records
  comments at all). Also confirmed live that a multi-line parameter list got collapsed onto one line, since
  `ast.unparse()` reformats whatever it touches regardless of the original layout. Fixed by splicing only the new
  `[T]`/`[**P]`/`[*Ts]` bracket into the function's original source right after its name, leaving every other byte
  - parameter list, defaults, line breaks, return type, docstring, body, comments - untouched:
  `renaissance.utils.unparse_utils.unparse_signature_only`, which also retired the docstring-indent workaround
  from python-ast-known-limitations.md item 4, since nothing but the bracket is ever regenerated via
  `ast.unparse()` any more.
- **Resolved: a nested closure referencing an enclosing function's type parameter used to be treated as an
  independent user, getting its own redundant (shadowing) type parameter added too** - which could corrupt the
  file outright when combined with the rewrite engine's dominance/suppression gap. Confirmed live against
  `starlette/starlette/authentication.py`'s `requires()` and its nested `websocket_wrapper`/`async_wrapper`/
  `sync_wrapper` closures. Fixed by attributing a type parameter's usage to the outermost function in its nesting
  chain (`type_var_domain.py`'s `functions_using_nodes`), since PEP 695 type parameters are already visible in
  nested closures via the same lexical scoping as any other enclosing-scope name.

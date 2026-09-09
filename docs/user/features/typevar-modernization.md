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
   (or there's no reference left at all), the recipe removes the declaration.
4. **Legacy `Unpack[T]` → `*T` rewrite (`TypeVarTupleCheck`).** A separate recipe, not a phase of the above:
   `Unpack[T]` and native `*T` unpacking are fully equivalent wherever `T` is a declared `TypeVarTuple` -
   `Unpack[T]` exists only because it's parseable on Pythons before the native syntax landed
   ([PEP 646](https://peps.python.org/pep-0646/), 3.11+). Every occurrence is rewritten with no per-occurrence
   safety analysis needed (unlike the PEP 695 conversion above, swapping syntax at one call site never changes
   semantics or visibility) - the only gate is the file-wide Python-version check, see
   [Python version gates](../concepts/python-version-gates.md).

Neither recipe drops the import it just made redundant (`TypeVar`, `Unpack`, ...) itself - that's `ruff`'s
`F401` rule's job, already solved there rather than duplicated; see API entry points below for where that
cleanup actually runs.

## Inputs

A single Python source file, passed by path.

## Outputs / effects

- The file is rewritten in place for every change classified as safe.
- `TypeVarCheck` returns `{"cross_file": {...}, "converted": {...}, "orphaned": {...}}`, each mapping
  `name -> "fixed" | "unsafe"`. `TypeVarTupleCheck` returns a single flat `{name -> "fixed" | "unsafe"}` (one
  phase, not three) - the CLI below merges it into the same result shape under an `"unpack_syntax"` key.
- Neither recipe removes the `from typing import ...` (or equivalent) name it makes redundant - see the
  User-facing summary above and the CLI's own `ruff check --fix --select F401` pass in API entry points below.

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
- **`TypeVarTupleCheck`'s `Unpack[T]` → `*T` rewrite only applies when the target declares Python 3.11+** (PEP
  646's true minimum - one version below `TypeVarCheck`'s own 3.12+ gate for PEP 695, deliberately not raised
  to match it, see [Python version gates](../concepts/python-version-gates.md)). Same conservative treatment as
  above: an unknown or too-low minimum reports every candidate `"unsafe"` and leaves the file untouched.
- `TypeVarTupleCheck` only recognizes a **module-level** `T = TypeVarTuple(...)` declaration in the same file -
  not one imported from a sibling module. When both recipes run together (the CLI below), `TypeVarTupleCheck`
  runs first specifically so the common case (a TypeVarTuple declared and used via `Unpack[T]` in the same file)
  composes correctly - `TypeVarCheck` removes a converted declaration once it PEP-695-converts it, and
  `TypeVarTupleCheck` needs that declaration to still be present to find the usage. One narrower case doesn't
  fully resolve in a single pass either way: a *cross-file-imported* `TypeVarTuple` used via `Unpack[T]` -
  `TypeVarCheck`'s own cross-file localization phase only runs after `TypeVarTupleCheck` has already looked (and
  found nothing, since the declaration wasn't local yet). Re-running the CLI a second time picks it up, since
  every phase is idempotent.

## Related concepts

- [Type parameter scope](../concepts/type-parameter-scope.md)

## Verified by test modules

- `test/refactoring/test_type_var_check.py`
- `test/refactoring/test_type_var_check_properties.py`
- `test/refactoring/test_type_var_tuple_check.py`
- `test/refactoring/test_type_var_tuple_check_properties.py`
- `test/rejuvenation/test_migration_type_recipes.py` (the CLI wrapper above)

## Implemented by code modules

- [Refactoring recipes](../../developer/modules/recipes.md)

## API entry points

```shell
rejuvenate refactor TypeVarCheck <file>
rejuvenate refactor TypeVarTupleCheck <file>
```

Equivalently, `PythonRefactoring.process("TypeVarCheck", file)` /
`PythonRefactoring.process("TypeVarTupleCheck", file)`.

A friendlier standalone CLI wraps both recipes together: `--help`, `--min-python` to override the detected
minimum target version (compared against each recipe's own true minimum - 3.12 for `TypeVarCheck`, 3.11 for
`TypeVarTupleCheck`), and a report distinguishing modified files from files with TypeVars it found but
couldn't safely convert. It writes changes for real - the target is always expected to be a git-tracked
checkout, so `git diff`/`git checkout` (or an editor's diff view) is the review-and-revert mechanism, not a
custom preview built into this tool. After processing every file, it runs `ruff check --fix --select F401`
once over every file it modified, dropping whichever imports either recipe's own rewrite made redundant -
see the User-facing summary above for why neither recipe drops that import itself.

```shell
python src/rejuvenation/migration-type-recipes.py <path> [--min-python MAJOR.MINOR] [--report PATH]
```

`<path>` may be a single `.py` file or a directory, scanned recursively (`.git`/`__pycache__`/`.venv`/`venv`
excluded). Run with `--help` for the full flag reference.

## Change considerations

- Supporting a future type-parameter-declaring construct means extending `_is_type_param_call` and
  `_build_type_param` in `type_var_domain.py` together.
- The cross-file phase only resolves same-directory imports; supporting package-qualified imports would need
  `_resolve_sibling_module` (also in `type_var_domain.py`) to handle dotted module names.
- The version gate (see Constraints above) only recognises versions in a known list (3.8 through 3.14, see
  `KNOWN_PYTHON_VERSIONS` in `renaissance/utils/python_version.py`); extending it to a new Python release means
  adding that release to the list.
- **Resolved: no CLI flag to override the detected minimum version.** `TypeVarCheck.min_python_override` existed
  only for tests until `migration-type-recipes.py`'s `--min-python MAJOR.MINOR` flag exposed it - see API entry
  points above.
- **Resolved: `TypeVarTupleCheck` used to only detect, never rewrite.** `find_legacy_unpack_usage()` still
  exists and still only detects (returns `list[str]`, unchanged, for any caller that just wants the names); the
  new `fix_legacy_unpack_usage()` is what `run()` now calls, and actually rewrites `Unpack[T]` to `*T` - see the
  User-facing summary and Constraints above. Consequence worth knowing: `rejuvenate refactor TypeVarTupleCheck
  <file>` (`PythonRefactoring.process()`) previously never wrote anything and now does - this is the intended
  effect of making the recipe actually fix code, not a bug, but it changes that entry point's existing behavior.
- **Resolved: both recipes used to remove their own now-unused import.** `TypeVarCheck` and `TypeVarTupleCheck`
  each had hand-rolled "is this import still used anywhere" logic, duplicating exactly what `ruff`'s `F401`
  already solves. Removed from both recipes; `migration-type-recipes.py` now runs `ruff check --fix --select
  F401` once over every file it modified instead - see API entry points above. A bare recipe invocation outside
  that CLI no longer gets this cleanup on its own.
- **Resolved: the CLI used to default to a dry-run preview, with `--apply` needed to write for real.** Dropped
  entirely, along with the `--diff` flag and the diff text the CLI used to print - the target is always a
  git-tracked checkout in practice, and `git diff`/`git checkout` (or an editor's diff view) review and revert
  changes better than a custom text diff this tool would otherwise have to build and maintain. The CLI now
  always writes for real; see API entry points above.
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

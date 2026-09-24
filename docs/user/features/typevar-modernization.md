# TypeVar modernization

{ #feature-typevar-modernization }

**Stable ID:** `FEATURE-TYPEVAR-MODERNIZATION`

## User-facing summary

Modernizes legacy `TypeVar`/`ParamSpec`/`TypeVarTuple` usage in a Python file end to end, in one command —
covering both what `ruff`'s `UP047` rule only offers as a separate, unsafe fix and a gap it doesn't detect or
clean up at all:

1. **Cross-file import localization.** A type parameter imported from another module in the target project
   (`from pkg.other_module import T`, `from .other_module import T`) is invisible to `ruff`'s `UP047` rule, which
   only looks at declarations in the
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

A Python file or directory, and the target project's minimum supported Python version (`--py`).

## Outputs / effects

- The file is rewritten in place for every change classified as safe.
- `TypeVarCheck` returns `{"cross_file": {...}, "converted": {...}, "orphaned": {...}}`, each mapping
  `name -> "fixed" | "unsafe"`. `TypeVarTupleCheck` returns a single flat `{name -> "fixed" | "unsafe"}` (one
  phase, not three) - the CLI below merges it into the same result shape under an `"unpack_syntax"` key.
- Neither recipe removes the `from typing import ...` (or equivalent) name it makes redundant - see the
  User-facing summary above and the CLI's own `ruff check --fix --select F401` pass in API entry points below.
- Alongside each phase's `"unsafe"` status, `TypeVarCheck` also records *why* on a matching instance attribute -
  `cross_file_unsafe_reasons`, `converted_unsafe_reasons`, `orphaned_unsafe_reasons` - and `TypeVarTupleCheck`
  records its own on `unsafe_reasons`; each maps `name -> UnsafeReason` (see Constraints below for the specific
  reasons). The CLI collects these into `FileReport.reasons` and prints the matching documented rule and link
  next to each unsafe name - see API entry points below.

## Constraints

Every case below is a distinct, permanent reason a candidate is reported `"unsafe"` and left untouched - each has
its own anchor so `migration-type-recipes.py --report` can link a specific occurrence straight to the rule that
explains it, rather than a generic "couldn't convert" message.

### PEP 695 version gate

{ #feature-typevar-modernization-pep695-version-gate }

[PEP 695](https://peps.python.org/pep-0695/) generic syntax (`def f[T](...)`) did not exist before Python 3.12
(released October 2023). If the minimum Python version passed with `--py` is below 3.12, every candidate is
reported `"unsafe"` and left untouched. Cross-file localization (phase 1) always runs, since it never introduces
PEP 695 syntax.

The cross-file phase resolves absolute and relative imports against the target directory passed to the CLI.
Imports that don't resolve to a file inside it (stdlib, third-party, re-exports through an intermediate
`__init__.py`, namespace packages) are silently out of scope, not reported unsafe.

**To fix this yourself:** if the project actually supports 3.12+, re-run with `--py 3.12` (or higher). If it
has to keep supporting older Pythons, there's no manual PEP 695 rewrite either, since the syntax doesn't exist
before 3.12.

### A declared TypeVar is exported via `__all__`

{ #feature-typevar-modernization-declared-typevar-exported }

A module-level `T = TypeVar(...)` (or `ParamSpec`/`TypeVarTuple`) listed in its own file's `__all__` is public
API - removing its declaration to convert it to PEP 695 syntax would break any importer still doing
`from this_module import T`. Left unconverted, `"unsafe"`. See
[Type parameter scope](../concepts/type-parameter-scope.md).

**To convert this yourself:** you have to accept the same trade-off the tool won't make automatically - remove
`T` from `__all__` (usually a breaking change for anything still importing it), move it into a PEP 695 signature
at every function that uses it, and delete the old `T = TypeVar(...)` line once every use site is converted. If
`T` can't be dropped from `__all__`, the declaration has to stay as it is.

### A declared TypeVar is used outside a function body

{ #feature-typevar-modernization-used-outside-function }

A module-level declaration referenced anywhere other than inside the function(s) being converted - for example
as a class's `Generic[T]` base, or in a module-level type alias - can't have its declaration removed: a PEP 695
type parameter only exists inside the function signature it's declared on, so that other use site would be left
referencing a name that no longer exists. Left unconverted, `"unsafe"`. See
[Type parameter scope](../concepts/type-parameter-scope.md).

**To convert this yourself:** check every other reference first (a `Generic[T]` base, a module-level type alias,
and so on) - a PEP 695 type parameter only exists inside the function signature that declares it, so it can't
back those other uses. If those other use sites can be rewritten or removed, the function signatures can then be
converted by hand and the module-level declaration deleted; otherwise it has to stay module-level.

### An imported TypeVar's origin module exports it via `__all__`

{ #feature-typevar-modernization-origin-module-exports-name }

Cross-file localization (phase 1) turns `from other_module import T` into a local `T = TypeVar(...)`
declaration. If `other_module` lists `T` in its own `__all__`, it's advertised as that module's public API -
localizing the import would leave two independent declarations of the same logical type parameter (the
original, still-exported one, and the new local copy), which silently breaks identity-based uses (e.g.
`isinstance` checks or generic subclassing across the two copies). Left as an import, `"unsafe"`.

**To fix this yourself:** localizing the import means also removing `T` from the *origin* module's `__all__`
(same public-API trade-off as the previous case, on the other file) - otherwise the two files end up with two
independent `T` objects, silently breaking anything relying on both referring to the same one.

### An imported TypeVar is used in an exported `Generic[...]` base at its origin

{ #feature-typevar-modernization-used-in-exported-generic-base }

If the origin module uses the imported name as a class's `Generic[T]` base, that class's own generic identity is
tied to this specific `T` object - localizing the import would create a second, unrelated `T`, breaking
subclassing or type-checking that depends on the two modules sharing the same type parameter. Left as an
import, `"unsafe"`.

**To fix this yourself:** the origin module's class is generic over this exact `T` object, so localizing the
import safely means converting that class - and anything downstream that depends on it - in the same
coordinated change, or the two modules end up with different, incompatible `T`s.

Supports `TypeVar` (including `bound=` and constraint forms), `ParamSpec`, and `TypeVarTuple`.

### A declared TypeVar is imported directly by another file in the target project

{ #feature-typevar-modernization-imported-elsewhere-in-project }

A module without `__all__` is still Python-legal to import any of its top-level names from directly -
`__all__` only governs `from module import *`, never `from module import specific_name`. So a declaration with
no `__all__` isn't automatically "unused elsewhere": before converting or removing it, the CLI (see API entry
points below) scans every file it was given for `from this_module import this_name`-shaped imports (absolute
or relative, resolved to the actual file - see `renaissance.utils.import_resolution`), and for the name read as
an attribute of the imported module (`import pkg.this_module` then `pkg.this_module.this_name`, or
`from pkg import this_module` then `this_module.this_name`). Any hit is treated as `"unsafe"`,
`IMPORTED_ELSEWHERE_IN_PROJECT`, regardless of `__all__`. A `from this_module import *` is not expanded, so a
name it pulls in is not detected. Running the recipe on a single file in
isolation (not via the CLI, or via the CLI on a lone file with no other files passed) has nothing to check
against, so this constraint can only fire when the target is a directory scanned alongside the files that
import from it.

**To convert this yourself:** the report only names the candidate, not the importing file - grep the project
for `from <this_module> import <name>` (absolute or relative) and `<this_module>.<name>` to find it. Once found, either update that
importer in the same change to get `name` from wherever it ends up after conversion, or leave the module-level
declaration as it is if the importer can't be updated alongside it - the same public-API trade-off as the
`__all__` case above, just surfaced by a direct import instead of an explicit `__all__` entry.

### PEP 646 version gate

{ #feature-typevar-modernization-pep646-version-gate }

`TypeVarTupleCheck`'s `Unpack[T]` → `*T` rewrite only applies when `--py` is 3.11+ (PEP
646's true minimum - one version below `TypeVarCheck`'s own 3.12+ gate for PEP 695, deliberately not raised
to match it, see [Python version gates](../concepts/python-version-gates.md)). Same conservative treatment as
the PEP 695 gate above: an unknown or too-low minimum reports every candidate `"unsafe"` and leaves the file
untouched.

**To fix this yourself:** if the project actually supports 3.11+, re-run with `--py 3.11` (or higher) - same
fix as the PEP 695 gate above, just at the lower threshold.

`TypeVarTupleCheck` only recognizes a **module-level** `T = TypeVarTuple(...)` declaration in the same file -
  not one imported from another module. When both recipes run together (the CLI below), `TypeVarTupleCheck`
  runs first specifically so the common case (a TypeVarTuple declared and used via `Unpack[T]` in the same file)
  composes correctly - `TypeVarCheck` removes a converted declaration once it PEP-695-converts it, and
  `TypeVarTupleCheck` needs that declaration to still be present to find the usage. One narrower case doesn't
  fully resolve in a single pass either way: a *cross-file-imported* `TypeVarTuple` used via `Unpack[T]` -
  `TypeVarCheck`'s own cross-file localization phase only runs after `TypeVarTupleCheck` has already looked (and
  found nothing, since the declaration wasn't local yet). Re-running the CLI a second time picks it up, since
  every phase is idempotent.

A declaration imported by other files in the target project is always kept at its origin during a run, even
when every importer gets localized in that same run. A second CLI run converts it, once no file imports it anymore.

Removing a declaration or an unused import leaves its surrounding blank lines behind, so a modified file can
start with, or contain, extra blank lines. Run your formatter afterwards to tidy them up.

## Related concepts

- [Type parameter scope](../concepts/type-parameter-scope.md)

## Verified by test modules

- `test/recipes/test_type_var_check.py`
- `test/recipes/test_type_var_check_convert.py`
- `test/recipes/test_type_var_check_localize.py`
- `test/recipes/test_type_var_check_orphaned.py`
- `test/recipes/test_type_var_check_properties.py`
- `test/recipes/test_type_var_tuple_check.py`
- `test/recipes/test_type_var_tuple_check_fix.py`
- `test/recipes/test_type_var_tuple_check_properties.py`
- `test/recipes/test_type_var_domain.py`
- `test/utils/test_import_resolution.py` - the project-wide import resolution the CLI uses for the
  `IMPORTED_ELSEWHERE_IN_PROJECT` constraint above
- `test/rejuvenation/test_migration_type_recipes.py` (the CLI wrapper above)

## Implemented by code modules

- [Refactoring recipes](../../developer/modules/recipes.md)

## API entry points

```shell
python src/rejuvenation/migration-type-recipes.py <path> --py MAJOR.MINOR [--report PATH]
```

- `<path>`: a `.py` file or a directory, scanned recursively (`.git`/`__pycache__`/`.venv`/`venv` excluded).
- `--py` (required): the minimum Python version the target project supports, not the one running the tool.
  PEP 695 rewrites need 3.12+, `*Ts` unpacking needs 3.11+.
- `--report`: also write the report to a file.

Runs `TypeVarTupleCheck`, then `TypeVarCheck`, on every file, then `ruff check --fix --select F401` on the files
it changed. Changes are written directly, so run it on a git checkout and review with `git diff`.

## Change considerations

- Supporting a future type-parameter-declaring construct means extending `_is_type_param_call` and
  `build_type_param` in `type_var_domain.py` together.
- Following re-exports through an intermediate `__init__.py`, or supporting namespace packages (PEP 420), means
  extending `resolve_project_module` in `renaissance/utils/import_resolution.py`.

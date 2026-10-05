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
   shared across several (`ruff` can't safely do this at all, since converting one function at a time never lets it
   confirm every use site is covered). The now-redundant module-level declaration is removed as part of the same
   pass.
3. **Orphaned declaration cleanup.** A defensive final pass for declarations left dead by outside means — e.g. a
   signature already converted to PEP 695 syntax by hand, or by running `ruff` before this recipe. `ruff`'s
   `UP047`, by its own documentation, never removes the module-level `T = TypeVar("T")` it makes redundant, in
   any case. Once every remaining reference to a declared name is shadowed by a same-named PEP 695 type parameter
   (or there's no reference left at all), the recipe removes the declaration.

The recipe doesn't drop the import it just made redundant (`TypeVar`, ...) itself - that's `ruff`'s `F401`
rule's job, already solved there rather than duplicated; see API entry points below for where that cleanup
actually runs.

A converted `TypeVarTuple` keeps its legacy `Unpack[Ts]` usages (`def f[*Ts](*args: Unpack[Ts])`), which is
valid as it is. To rewrite them to native `*Ts` syntax, run `ruff`'s `UP044` rule afterwards; see
[Rejected recipes](../../developer/modules/rejected-recipes.md) for why the tool doesn't do this itself.

## Inputs

A Python file or directory, and the target project's minimum supported Python version (`--py`).

Supports `TypeVar` (including `bound=` and constraint forms), `ParamSpec`, and `TypeVarTuple` declarations.

The cross-file phase resolves absolute and relative imports against the target directory passed to the CLI (the
file's own folder when a single file is passed). Imports that don't resolve to a file inside it (stdlib,
third-party, re-exports through an intermediate `__init__.py`, namespace packages) are silently out of scope, not
reported unsafe.

## Outputs / effects

- The file is rewritten in place for every change classified as safe.
- `TypeVarCheck` returns `{"cross_file": {...}, "converted": {...}, "orphaned": {...}}`, each mapping
  `name -> "fixed" | "unsafe"`.
- The recipe doesn't remove the `from typing import ...` (or equivalent) name it makes redundant - see the
  User-facing summary above and the CLI's own `ruff check --fix --select F401` pass in API entry points below.
- Alongside each phase's `"unsafe"` status, `TypeVarCheck` also records *why* on a matching instance attribute -
  `cross_file_unsafe_reasons`, `converted_unsafe_reasons`, `orphaned_unsafe_reasons` - each mapping
  `name -> UnsafeReason` (see Constraints below for the specific reasons). The CLI collects these into
  `FileReport.reasons` and prints the matching documented rule and link next to each unsafe name - see API entry
  points below.

## Constraints

Every case below is a distinct, permanent reason a candidate is reported `"unsafe"` and left untouched - each has
its own anchor so the CLI's report (printed on every run, and also saved to a file by `--report`) can link a
specific occurrence straight to the rule that explains it, rather than a generic "couldn't convert" message.

### PEP 695 version gate

{ #feature-typevar-modernization-pep695-version-gate }

[PEP 695](https://peps.python.org/pep-0695/) generic syntax (`def f[T](...)`) did not exist before Python 3.12
(released October 2023). If the minimum Python version passed with `--py` is below 3.12, every candidate is
reported `"unsafe"` by the conversion phase (phase 2) and left untouched. Cross-file localization (phase 1) and
the orphaned-declaration cleanup (phase 3) still run, since neither introduces PEP 695 syntax.

**To fix this yourself:** if the project actually supports 3.12+, re-run with `--py 3.12` (or higher). If it
has to keep supporting older Pythons, there's no manual PEP 695 rewrite either, since the syntax doesn't exist
before 3.12.

### A declared TypeVar is exported via `__all__`

{ #feature-typevar-modernization-declared-typevar-exported }

A module-level `T = TypeVar(...)` (or `ParamSpec`/`TypeVarTuple`) listed in its own file's `__all__` is public
API - removing its declaration to convert it to PEP 695 syntax would break any importer still doing
`from this_module import T`. Left unconverted, `"unsafe"`.

**To convert this yourself:** you have to accept the same trade-off the tool won't make automatically - remove
`T` from `__all__` (usually a breaking change for anything still importing it), move it into a PEP 695 signature
at every function that uses it, and delete the old `T = TypeVar(...)` line once every use site is converted. If
`T` can't be dropped from `__all__`, the declaration has to stay as it is.

### A declared TypeVar is used outside a function body

{ #feature-typevar-modernization-used-outside-function }

A module-level declaration referenced anywhere other than inside the function(s) being converted - for example
as a class's `Generic[T]` base, or in a module-level type alias - can't have its declaration removed: a PEP 695
type parameter only exists inside the function signature it's declared on, so that other use site would be left
referencing a name that no longer exists. Left unconverted, `"unsafe"`.

**To convert this yourself:** check every other reference first (a `Generic[T]` base, a module-level type alias,
and so on). If those other use sites can be rewritten or removed, the function signatures can then be converted
by hand and the module-level declaration deleted; otherwise it has to stay module-level.

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

### An imported TypeVar is used in a `Generic[...]` base at its origin

{ #feature-typevar-modernization-used-in-exported-generic-base }

If the origin module uses the imported name as a class's `Generic[T]` base, that class's own generic identity is
tied to this specific `T` object - localizing the import would create a second, unrelated `T`, breaking
subclassing or type-checking that depends on the two modules sharing the same type parameter. Left as an
import, `"unsafe"`. Any class in the origin module counts, exported or not, but only a bare `Generic[...]` base
is detected: `typing.Generic[...]` and other generic bases such as `Protocol[T]` are not.

**To fix this yourself:** the origin module's class is generic over this exact `T` object, so localizing the
import safely means converting that class - and anything downstream that depends on it - in the same
coordinated change, or the two modules end up with different, incompatible `T`s.

### An imported TypeVar's origin module imports its constructor conditionally

{ #feature-typevar-modernization-origin-imports-constructor-conditionally }

A localized declaration is a copy of the origin's `T = TypeVar(...)` call, so it runs with whichever `TypeVar`
the *importing* file has in scope. If the origin imports `TypeVar` (or `ParamSpec`/`TypeVarTuple`) inside a
module-level `if` or `try` block - typically `typing` on newer Pythons and `typing_extensions` below, because
the declaration uses an argument such as `default=` that older `typing` versions reject - the copy may bind a
different implementation than the origin intended and fail at import time on some supported versions. Left as
an import, `"unsafe"`.

**To fix this yourself:** give the importing file the same conditional import as the origin before copying the
declaration across, or leave the import as it is.

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

A declaration imported by other files in the target project is always kept at its origin during a run, even
when every importer gets localized in that same run. A second CLI run converts it, once no file imports it anymore.

A single import statement that brings in two or more localizable type parameters (`from .origin import T, U`)
currently makes the localization phase fail for that file: it is reported under `ERRORS` and left unchanged,
because two rewrites are queued on the same statement. Splitting it into one import per name
(`from .origin import T` and `from .origin import U`) lets the next run localize both.

A function whose body contains a multi-line string literal with a continuation line indented less than the body
(for example at column 0) is converted with the contents of that literal changed and the body re-indented; the
tool does not report it. Review modified files with `git diff`, or convert such functions by hand. See
[Python AST known limitations](../../developer/modules/python-ast-known-limitations.md).

Removing a declaration or an unused import leaves its surrounding blank lines behind, so a modified file can
start with, or contain, extra blank lines. Run your formatter afterwards to tidy them up.

## Related concepts

- [Python version gates](../concepts/python-version-gates.md)

## Verified by test modules

- `test/recipes/test_type_var_check.py`
- `test/recipes/test_type_var_check_convert.py`
- `test/recipes/test_type_var_check_localize.py`
- `test/recipes/test_type_var_check_orphaned.py`
- `test/recipes/test_type_var_check_properties.py`
- `test/recipes/test_type_var_domain.py`
- `test/recipes/test_step_runner.py` - the step runner the CLI uses for the three phases
- `test/recipes/test_python_refactoring.py` - `find_rst_node` and `narrowed_import_text`, used by the recipe
- `test/recipes/conftest.py` - the fixtures that build the recipe in the tests above
- `test/utils/test_unparse_utils.py` - the bracket splice that adds the PEP 695 type parameters to a signature
- `test/utils/test_import_resolution.py` - the project-wide import resolution the CLI uses for the
  `IMPORTED_ELSEWHERE_IN_PROJECT` constraint above
- `test/rejuvenation/test_migration_type_recipes.py` (the CLI wrapper above)

## Implemented by code modules

- [Refactoring recipes](../../developer/modules/recipes.md)
- `src/renaissance/recipes/type_var_check.py`, `type_var_domain.py`, `step_runner.py` and `python_refactoring.py`
- `src/renaissance/utils/import_resolution.py` and `unparse_utils.py`
- `src/rejuvenation/migration-type-recipes.py` (the CLI)

## API entry points

```shell
python src/rejuvenation/migration-type-recipes.py <path> --py MAJOR.MINOR [--report PATH] [--no-ruff]
```

- `<path>`: a `.py` file or a directory, scanned recursively (`.git`/`__pycache__`/`.venv`/`venv` excluded).
- `--py` (required): the minimum Python version the target project supports, not the one running the tool.
  PEP 695 rewrites need 3.12+.
- `--report`: also write the report to a file. The same report is always printed to the console.
- `--no-ruff`: skip the final `ruff` pass, leaving every unused import in the modified files in place, including
  the ones the recipe made unused.

Runs `TypeVarCheck` on every file, then `ruff check --fix --select F401` on the files it changed (unless
`--no-ruff` is passed). That pass removes every import `ruff` reports as unused in those files, including
imports that were already unused before the run. `ruff` is invoked as `python -m ruff`, so it has to be
installed in the same environment as the tool; if it can't run, the files keep the recipe's output and
the report line still says the pass ran. Changes are written directly, so run it on a git checkout and review
with `git diff`.

The report has a summary line, then the `MODIFIED`, `NEEDS MANUAL REVIEW` (each unsafe name with its documented
rule and link) and `ERRORS` sections; files with no type-parameter usage are only counted. The exit code is 0 on
normal completion (files needing manual review are not a failure), 2 for a usage error such as a missing path or
a malformed `--py`, and 3 if any file raised an unhandled exception, which is listed under `ERRORS`.

## Change considerations

- Supporting a future type-parameter-declaring construct means extending `_is_type_param_call` and
  `build_type_param` in `type_var_domain.py` together.
- Following re-exports through an intermediate `__init__.py`, or supporting namespace packages (PEP 420), means
  extending `resolve_project_module` in `renaissance/utils/import_resolution.py`.

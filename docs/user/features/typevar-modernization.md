# TypeVar modernization { #feature-typevar-modernization }

**Stable ID:** `FEATURE-TYPEVAR-MODERNIZATION`

## User-facing summary

Modernizes legacy `TypeVar`/`ParamSpec`/`TypeVarTuple` usage in a Python file end to end, in one command —
covering both what `ruff`'s `UP047` rule only offers as a separate, unsafe fix and a gap it doesn't detect or
clean up at all:

1. **Cross-file import localization.** A type parameter imported from another module in the target project
   (`from pkg.other_module import T`, `from .other_module import T`) is invisible to `ruff`'s `UP047` rule, which
   only looks at declarations in the
   same file. Where safe, the recipe rewrites the import into an equivalent local declaration: an exact copy of the
   origin's declaration (bound, constraints, variance and default included), importing from the origin any name
   its arguments use (`bound=Shape`).
2. **Conversion to PEP 695 syntax.** Every declared `TypeVar`/`ParamSpec`/`TypeVarTuple` is rewritten to
   [PEP 695](https://peps.python.org/pep-0695/) generic syntax (`def f[T](...)`) across every function that uses
   it — whether it's used by one function (the same rewrite `ruff` offers, but only via `--unsafe-fixes`) or
   shared across several (`ruff` can't safely do this at all, since converting one function at a time never lets it
   confirm every use site is covered). A function is converted even when the name is also used outside functions
   (a `Generic[T]` base, a module-level alias): its own `[T]` means the same thing there. The methods of a class
   that is generic over the name are left alone, since their `T` is the class's. A declaration's bound,
   constraints and `default=` are carried over (`T = TypeVar("T", bound=str, default=str)` becomes
   `def f[T: str = str](...)`), and `infer_variance=True` needs nothing, since a PEP 695 type parameter always
   infers its variance. A declaration passing an argument with no PEP 695 equivalent, such as `covariant=True`,
   is left untouched (see Constraints below). Type parameters with a default are placed after those without
   one, as Python requires. This phase only adds the type parameters; the module-level
   declaration is removed by the next one once nothing uses it anymore.
3. **Orphaned declaration cleanup.** Removes every module-level declaration nothing uses anymore: the ones phase 2
   just made redundant, and ones left dead by outside means - e.g. a signature already converted to PEP 695
   syntax by hand, or by running `ruff` before this recipe; `ruff`'s `UP047`, by its own documentation, never
   removes the module-level `T = TypeVar("T")` it makes redundant. A declaration counts as dead once every
   remaining reference to it is shadowed by a same-named PEP 695 type parameter on a function, including one
   enclosing it (or there's no reference left at all).

The recipe doesn't drop the import it just made redundant (`TypeVar`, ...) itself - that's `ruff`'s `F401`
rule's job, already solved there rather than duplicated; see API entry points below for where that cleanup
actually runs.

A converted `TypeVarTuple` keeps its legacy `Unpack[Ts]` usages (`def f[*Ts](*args: Unpack[Ts])`), which is
valid as it is. To rewrite them to native `*Ts` syntax, run `ruff`'s `UP044` rule afterwards; see
[Rejected recipes](../../developer/modules/rejected-recipes.md) for why the tool doesn't do this itself.

## Inputs

A Python file or directory, and the target project's minimum supported Python version (`--py`).

Supports `TypeVar` (including `bound=`, constraint and `default=` forms), `ParamSpec` and `TypeVarTuple`
(including `default=`) declarations.

The cross-file phase resolves absolute and relative imports against the target directory passed to the CLI (the
file's own folder when a single file is passed). Imports that don't resolve to a file inside it (stdlib,
third-party, re-exports through an intermediate `__init__.py`, namespace packages) are silently out of scope, not
reported unsafe. So is an import that renames the type parameter (`from .origin import T as U`): it is left as
it is, and a file whose only type parameters arrive that way is counted as clean.

### Generic classes { #feature-typevar-modernization-generic-class }

A class is *generic over* `T` when `T` is one of its type parameters, in one of two ways
([PEP 484](https://peps.python.org/pep-0484/#user-defined-generic-types),
[PEP 695](https://peps.python.org/pep-0695/)):

1. **Declared:** the class declares its own `T` as a PEP 695 type parameter (`class Box[T]:`).
2. **Inherited:** `T` appears in one of its bases - `Generic[T]`, `typing.Generic[T]`, `Protocol[T]`,
   `Mapping[T]`, `Base[int, T]` - and the class doesn't declare its own `T`.

Inside such a class, `T` in a method means the class's parameter, so the tool never adds `[T]` to the class's
methods. A generic class at the origin of an import doesn't stop the import from being localized: the class keeps
its own `T`, and the importing file's functions resolve their copy of `T` in their own scope.

## Outputs / effects

- The file is rewritten in place for every change classified as safe.
- `TypeVarCheck` returns `{"cross_file": {...}, "converted": {...}, "orphaned": {...}}`, each mapping
  `name -> "fixed" | "unsafe"`.
- The recipe doesn't remove the `from typing import ...` (or equivalent) name it makes redundant - see the
  User-facing summary above and the CLI's own `ruff check --fix --select F401` pass in API entry points below.
- Alongside each phase's `"unsafe"` status, `TypeVarCheck` also records *why* on a matching instance attribute -
  `cross_file_unsafe_reasons`, `converted_unsafe_reasons` and `orphaned_unsafe_reasons` - each mapping
  `name -> UnsafeReason` (see Constraints below for the specific reasons). The CLI collects these into
  `FileReport.reasons` and prints the matching documented rule and link next to each unsafe name - see API entry
  points below.

## Constraints

Every case below is a distinct, permanent reason a candidate is reported `"unsafe"` - each has
its own anchor so the CLI's report (printed on every run, and also saved to a file by `--report`) can link a
specific occurrence straight to the rule that explains it, rather than a generic "couldn't convert" message.

### PEP 695 version gate { #feature-typevar-modernization-pep695-version-gate }

[PEP 695](https://peps.python.org/pep-0695/) generic syntax (`def f[T](...)`) did not exist before Python 3.12
(released October 2023). If the minimum Python version passed with `--py` is below 3.12, every candidate that
needs PEP 695 syntax is reported `"unsafe"` by the conversion phase (phase 2) and left untouched. Cross-file
localization (phase 1) and the orphaned-declaration cleanup (phase 3) still run, since neither introduces PEP 695
syntax.

**To fix this yourself:** if the project actually supports 3.12+, re-run with `--py 3.12` (or higher). If it
has to keep supporting older Pythons, there's no manual PEP 695 rewrite either, since the syntax doesn't exist
before 3.12.

### PEP 696 version gate { #feature-typevar-modernization-pep696-version-gate }

A declaration passing `default=` (`T = TypeVar("T", default=int)`, also accepted by `ParamSpec` and
`TypeVarTuple`) converts to a type parameter default, `def f[T = int](...)`, which is
[PEP 696](https://peps.python.org/pep-0696/) syntax and did not exist before Python 3.13. On a 3.13+ target the
default is carried over into the converted signature. Below 3.13 that declaration is reported `"unsafe"` and
left untouched, since converting it **without** its default would silently change what a type checker infers
(for example, a call returning `list[T]` that leaves `T` unsolved goes from `list[int]` to a bare `list` in
pyright). Other declarations in the
same file are unaffected.

**To fix this yourself:** re-run with `--py 3.13` (or higher) if the project supports it. Otherwise keep the
module-level declaration; there's no 3.12 syntax that expresses a type parameter default.

### A declaration passes an argument with no PEP 695 equivalent { #feature-typevar-modernization-no-pep695-equivalent }

Conversion carries over a declaration's bound, constraints, `default=` and `infer_variance=True` (a PEP 695
type parameter always infers its variance). An argument the `[...]` syntax has no way to write would be lost,
so a declaration passing one is reported `"unsafe"` and left untouched instead:

- **Explicit variance**, `covariant=` or `contravariant=`: PEP 695 has no syntax to declare variance.
- **`bound=` on a `ParamSpec` or `TypeVarTuple`**: accepted at runtime (on `TypeVarTuple` since Python 3.15),
  but `[**P: X]` and `[*Ts: X]` are a `SyntaxError`. Its meaning is not defined yet either, see
  [PEP 612](https://peps.python.org/pep-0612/) and the
  [`typing` documentation](https://docs.python.org/3.15/library/typing.html#typing.TypeVarTuple).
- **A `**mapping` of options**, whose contents the tool can't see.
- **A keyword added by a later Python version.**

**To fix this yourself:** decide whether the argument matters. A type parameter used only by functions gets
nothing from `covariant=`/`contravariant=`, since variance only affects generic classes; if that's the case,
drop it from the declaration and re-run. Otherwise keep the module-level declaration.

### A declared TypeVar is exported via `__all__` { #feature-typevar-modernization-declared-typevar-exported }

A module-level `T = TypeVar(...)` (or `ParamSpec`/`TypeVarTuple`) listed in its own file's `__all__` is public
API - removing its declaration would break any importer still doing `from this_module import T`. The functions
using it are still converted (each gets its own `[T]`), but the declaration is kept and reported `"unsafe"` by
the orphaned-declaration cleanup.

**To remove it yourself:** drop `T` from `__all__` (usually a breaking change for anything still importing it),
then delete the `T = TypeVar(...)` line. If `T` can't be dropped from `__all__`, the declaration has to stay.

### A declared TypeVar is only used inside a generic class { #feature-typevar-modernization-used-in-generic-class }

A class generic over `T` (see Generic classes above), declared (`class Box[T]:`, for example
after `ruff`'s `UP046`, which leaves the old `T = TypeVar("T")` behind) or inherited (`Generic[T]`,
`Protocol[T]`, `Base[T]`). Inside that class, `T` is the class's own parameter, so adding `[T]` to one of its
methods would give the method a second, unrelated `T` and change what its signature means. The tool
never touches those methods, the class or the declaration. When nothing else uses `T`, there is nothing left to
convert and the name is reported `"unsafe"`; when standalone functions also use it, those are converted.

**To fix this yourself:** for a `Generic[T]`-style class, `ruff`'s `UP046` can rewrite it to `class Box[T]:`.
Once the class declares `T` itself and nothing else uses the module-level `T`, delete the old
`T = TypeVar("T")` line.

### A name the declaration uses can't be imported here { #feature-typevar-modernization-declaration-name-unavailable }

A localized declaration is a copy of the origin's, and the names its arguments use (`bound=Shape`, constraints,
`default=`) are imported from the origin. That's only possible when the origin binds the name at module level at
runtime, and only correct when the importing file doesn't already bind it to something else. If the origin only
imports it for type checking (`if TYPE_CHECKING:`, typically with `bound="Shape"`), importing it from there would
fail at runtime; if the importing file has its own `class Shape`, or a `Shape` from another module, the copy would
silently refer to that other object. Left as an import, `"unsafe"`.

**To fix this yourself:** import the name the same way the origin does (for example under `if TYPE_CHECKING:`)
or rename one of the two names, then write the local declaration by hand.

### The origin imports the TypeVar constructor conditionally { #feature-typevar-modernization-origin-imports-constructor-conditionally }

A localized declaration is a copy of the origin's `T = TypeVar(...)` call, so it runs with whichever `TypeVar`
the *importing* file has in scope. If the origin imports `TypeVar` (or `ParamSpec`/`TypeVarTuple`) inside a
module-level `if` or `try` block - typically `typing` on newer Pythons and `typing_extensions` below, because
the declaration uses an argument such as `default=` that older `typing` versions reject - the copy may bind a
different implementation than the origin intended and fail at import time on some supported versions. Left as
an import, `"unsafe"`.

**To fix this yourself:** give the importing file the same conditional import as the origin before copying the
declaration across, or leave the import as it is.

### A declared TypeVar is imported by another project file { #feature-typevar-modernization-imported-elsewhere-in-project }

A module without `__all__` is still Python-legal to import any of its top-level names from directly -
`__all__` only governs `from module import *`, never `from module import specific_name`. So a declaration with
no `__all__` isn't automatically "unused elsewhere": before removing it, the CLI (see API entry
points below) scans every file it was given for `from this_module import this_name`-shaped imports (absolute
or relative, resolved to the actual file - see `renaissance.utils.import_resolution`), and for the name read as
an attribute of the imported module (`import pkg.this_module` then `pkg.this_module.this_name`, or
`from pkg import this_module` then `this_module.this_name`). Any hit keeps the declaration, `"unsafe"`,
`IMPORTED_ELSEWHERE_IN_PROJECT`, regardless of `__all__`; the functions using it are still converted. A
`from this_module import *` is not expanded, so a
name it pulls in is not detected. Running the recipe on a single file in
isolation (not via the CLI, or via the CLI on a lone file with no other files passed) has nothing to check
against, so this constraint can only fire when the target is a directory scanned alongside the files that
import from it.

**To remove it yourself:** the report only names the candidate, not the importing file - grep the project for
`from <this_module> import <name>` (absolute or relative) and `<this_module>.<name>` to find it. Once that importer
no longer needs it, a second run of the tool removes the declaration.

A declaration imported by other files in the target project is always kept at its origin during a run, even
when every importer gets localized in that same run. A second CLI run removes it, once no file imports it anymore.

A single import statement that brings in two or more localizable type parameters (`from .origin import T, U`)
currently makes the localization phase fail for that file: it is reported under `ERRORS` and left unchanged,
because two rewrites are queued on the same statement. Splitting it into one import per name
(`from .origin import T` and `from .origin import U`) lets the next run localize both.

A function whose body contains a multi-line string literal with a continuation line indented less than the body
(for example at column 0) is converted with the contents of that literal changed and the body re-indented; the
tool does not report it. Review modified files with `git diff`, or convert such functions by hand. See
[Python AST known limitations](../../developer/modules/python-ast-known-limitations.md).

A declaration whose `default=` uses another legacy declaration (`U = TypeVar("U", default=T)`) is converted
with that default as it is, so `def f[U = T](...)` refers to the module-level `T` rather than a type parameter
of the function. The tool does not report it; review such functions with `git diff` and correct the converted
signature by hand, adding `T` to the same bracket before `U` (`def f[T, U = T](...)`).

A localized type parameter is a new object with the same definition as the origin's. Type checkers treat it the
same, but runtime code that compares type parameters by identity (for example `MyBox.__parameters__[0] is
origin.T`) sees two different objects. A file that imports `T` from a file the tool localized (directly or
through its `__all__`) receives that copy too.

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
- `test/recipes/test_step_runner.py` - the step runner `TypeVarCheck.check()` uses for its three phases
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
  PEP 695 rewrites need 3.12+, and type parameter defaults (PEP 696) 3.13+.
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
rule and link) and `ERRORS` sections; files with no type-parameter usage are only counted. Under `MODIFIED`, a
name listed as converted isn't repeated under orphaned, since its declaration is removed as part of the same run.
The exit code is 0 on
normal completion (files needing manual review are not a failure), 2 for a usage error such as a missing path or
a malformed `--py`, and 3 if any file raised an unhandled exception, which is listed under `ERRORS`.

## Change considerations

- Supporting a future type-parameter-declaring construct means extending `_is_type_param_call` and
  `build_type_param` in `type_var_domain.py` together.
- A constructor keyword added by a later Python version is refused (`NO_PEP695_EQUIVALENT`) until
  it is added to `_CONVERTIBLE_KEYWORDS` in `type_var_domain.py` and carried over by `build_type_param`. The
  same applies if PEP 695 syntax ever gains a way to write variance, or a bound on `**P`/`*Ts`.
- Following re-exports through an intermediate `__init__.py`, or supporting namespace packages (PEP 420), means
  extending `resolve_project_module` in `renaissance/utils/import_resolution.py`.

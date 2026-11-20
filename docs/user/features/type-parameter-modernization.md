<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Type parameter modernization { #feature-type-parameter-modernization }

**Stable ID:** `FEATURE-TYPE-PARAMETER-MODERNIZATION`

## User-facing summary

Rewrites legacy [type parameter](../concepts/type-parameters.md) declarations (`TypeVar`, `ParamSpec` and
`TypeVarTuple`) to [PEP 695](https://peps.python.org/pep-0695/) syntax across a project. `ruff`'s `UP047` only does
part of this: it skips imported type parameters, nested functions and (outside preview) `default=`, and keeps the old
declaration.

**Before:**

```python
# shapes.py
from typing import TypeVar

T = TypeVar("T", bound=int)

# main.py
from shapes import T


def first(items: list[T]) -> T: ...
```

**After:** `main.py` holds `def first[T: int](items: list[T]) -> T: ...`, and `shapes.py` no longer declares `T`.
On xarray, the tool converted type parameters in 8 files
([pydata/xarray#11768](https://github.com/pydata/xarray/pull/11768/commits/bb6033218eee48be64aba921265e3dd4e5aea106)).

The tool runs four phases on each file:

1. **Localize.** An import of a type parameter from another project file (`from shapes import T`) is replaced by a copy
   of its declaration.
2. **Convert.** Every function whose signature uses a declared type parameter gets its own `[T]`, with bound,
   constraints and `default=` (`def f[T: str = str](...)`). `covariant=` and `contravariant=` (on `TypeVar` and
   `ParamSpec`) are dropped. A nested function gets no `[T]` when an enclosing function uses `T` too, and neither do
   methods of a class generic over `T` (`class Box[T]`, `Generic[T]`, `Protocol[T]`).
3. **Remove.** A module-level declaration that nothing uses any more is deleted, including one left behind by `ruff`'s
   `UP046` or `UP047`.
4. **Drop the underscore.** `def f[_T](x: _T)` becomes `def f[T](x: T)`. `ruff`'s `UP049` does this too, but
   together with `UP047` it can leave the uses as `_T`
   ([astral-sh/ruff#21004](https://github.com/astral-sh/ruff/issues/21004)).

Files are processed origins first, and again while the names other files import from them change. A declaration left
unused by localization is therefore removed in the same run.

## Inputs

A `.py` file or a directory, and `--py`, the oldest Python version the project supports (see *API entry points*).

Imports are resolved against `<path>` (in a `src/` layout, pass `src/`). Only a module-level `from X import T`, where
`X` is a file under `<path>`, is localized. These imports stay, and the origin keeps its declaration:

- imports from outside `<path>`;
- imports inside an `if` or `try` block, or inside a function;
- a renamed import (`from shapes import T as U`);
- a re-export through an `__init__.py` that keeps its own import, for example because its `__all__` lists `T`.

### Shared declaration files { #feature-type-parameter-modernization-ignore }

The tool cannot see other projects, so a declaration that nothing in the project uses is removed, unless `__all__`
lists it. To keep a shared file such as `types.py`, name it with `--ignore FILE...`, relative to `<path>`. The file is
not processed, and files importing from it keep that import, so their functions using it are not converted.

```shell
python src/rejuvenation/migration_type_recipes.py ./some_repo --py 3.12 --ignore pkg/types.py pkg/aliases.py
```

Put `<path>` before `--ignore`, which takes every value after it.

### Disabling localization { #feature-type-parameter-modernization-no-localization }

A localized `T` is a copy, a different object from the original, so code that compares type parameters with `is`
sees two objects. `--no-localization` keeps every project import of a type parameter, so the functions using it are not
converted. Unlike `--ignore`, every file is still processed.

```shell
python src/rejuvenation/migration_type_recipes.py ./some_repo --py 3.12 --no-localization
```

## Outputs / effects

- Files are changed in place, then cleaned up by the `ruff` step (see *The `ruff` step*).
- With `--report`, each refused change is listed with its reason (see *Constraints*). Without it, refusals only appear
  in the commit message, which is printed only when a file changed.
- A file under `ERRORS` may be partly changed, since each phase is saved before the next one runs. A file that is not
  valid UTF-8 is listed there with its `UnicodeDecodeError`, and left unchanged.

### Known limitations

The report does not explain these cases, so check the result with `git diff`. Their causes are in
[Refactoring recipes](../../developer/modules/recipes.md#non-goals).

**Can break code:**

| Input                                                                                                   | Result                                                                           |
| ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `@cache_on(T)` or `def f(x: list[T], default=T)`                                                        | Declaration removed: `NameError` on import                                       |
| Importer with `from shapes import *`                                                                    | Declaration removed from `shapes.py`: `NameError` in the importer                |
| `__all__.append("T")` or `__all__.extend(["T"])`                                                        | Declaration removed, although it is exported                                     |
| `A: TypeAlias = "list[T]"`                                                                              | Declaration removed, while the string still names `T`                            |
| `from pkg.shapes import T`, with `<path>` above `src/`                                                  | Declaration removed: `ImportError` in the importer                               |
| Origin with `from typing import *`, when the copy is kept (for a `Generic[T]` base)                     | Copy without a `TypeVar` import: `NameError`                                     |
| `T = U = TypeVar("T")`                                                                                  | `U` is left undefined                                                            |
| `V = TypeVar("W")`                                                                                      | `def f(x: V) -> V` becomes `def f[W](x: V) -> V`                                 |
| `U = TypeVar("U", default=T)`, in a function that does not use `T`                                      | `def f[U = T]`, where `T` is still the module-level one                          |
| `def f(a: AnyStr, b: T)`                                                                                | `def f[T](a: AnyStr, b: T)`, which type checkers reject for mixing both syntaxes |
| A file starting with a UTF-8 byte order mark ([#153](https://github.com/TNO/Renaissance.Py/issues/153)) | Code corrupted, file listed under `ERRORS`                                       |
| `T = TypeVar("T"); x = 1` or `import os; from shapes import T`                                          | Invalid syntax written, file listed under `ERRORS`                               |

**Cosmetic or operational:**

| Case                                                                                      | Result                                                                                                                                       |
| ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `T = typing.TypeVar("T")`                                                                 | Not recognised, the file counts as clean                                                                                                     |
| `X = TypeVar(name)`                                                                       | File listed under `ERRORS`, nothing changed                                                                                                  |
| `Unpack[Ts]`                                                                              | Left as it is. `ruff`'s `UP044` rewrites it to `*Ts` (see [Rejected recipes](../../developer/modules/rejected-recipes.md))                   |
| `requires-python` in `pyproject.toml`                                                     | Not read: `--py` decides which syntax is written                                                                                             |
| Comment lines above a moved or removed declaration                                        | Not copied, or left behind ([#189](https://github.com/TNO/Renaissance.Py/issues/189)); a comment on the declaration's own line moves with it |
| An existing type parameter bracket split over lines                                       | Rebuilt on one line, without its comments                                                                                                    |
| A localized declaration whose constructor this file already imports from another module   | A second import of the constructor shadows the first                                                                                         |
| `_T` refused in one function of a file                                                    | Kept in the file's other functions too, or renamed there while the report lists `_T` only for review                                         |
| `--no-ruff`                                                                               | Added imports are not merged or sorted; unused imports and extra blank lines stay                                                            |
| CRLF line endings                                                                         | A changed file is written back with LF                                                                                                       |
| `--report` in a directory that does not exist                                             | The run stops after the files are rewritten, and no report is written                                                                        |

## Constraints

Each case below stops one change. With `--report`, it is listed under `NEEDS MANUAL REVIEW` with this message:

| Report message                                                                 | Section                                  |
| ------------------------------------------------------------------------------ | ---------------------------------------- |
| Declares a default= (PEP 696), …                                               | *PEP 696 version gate*                   |
| Declaration passes an argument with no PEP 695 equivalent, …                   | *No PEP 695 equivalent*                  |
| Every function using it also uses a type variable that can't be converted      | *Shares a function with a refused one*   |
| Exported via `__all__`                                                         | *Exported via `__all__`*                 |
| Only used inside a class that is generic over it                               | *Only used inside a generic class*       |
| Declaration uses a name that isn't available at module level …                 | *Name not available at module level*     |
| Origin module imports TypeVar/ParamSpec/TypeVarTuple inside an if/try block, … | *Origin imports `TypeVar` conditionally* |
| Imported directly by another file in the target project                        | *Imported by another project file*       |
| Name without its leading underscore is already used …                          | *New name not free*                      |
| A use of it is written in a form the tool can't rewrite, …                     | *Use cannot be rewritten*                |

### Python version gates { #feature-type-parameter-modernization-version-gates }

`--py` is the oldest Python version the project supports, not the one running the tool. It must be 3.12 or higher,
since [PEP 695](https://peps.python.org/pep-0695/) syntax is a `SyntaxError` before that. Syntax from a later PEP is
only written when `--py` allows it.

#### PEP 696 version gate { #feature-type-parameter-modernization-pep696-version-gate }

A `default=` needs Python 3.13 ([PEP 696](https://peps.python.org/pep-0696/)). Below that, the declaration and the
functions using it are not converted, since dropping the default would change what type checkers infer.

```python
T = TypeVar("T", default=int)


def first(items: list[T]) -> T: ...
```

With `--py 3.13` this becomes `def first[T = int](items: list[T]) -> T: ...`. With `--py 3.12` the file is unchanged.

**What to do:** run again with `--py 3.13` if the project supports it. Otherwise keep the declaration.

### No PEP 695 equivalent { #feature-type-parameter-modernization-no-pep695-equivalent }

The `[...]` syntax cannot write a `bound=` on a `ParamSpec` or `TypeVarTuple`, `covariant=` or `contravariant=` on a
`TypeVarTuple`, a `**mapping` of options, or a keyword added by a later Python version.

```python
P = ParamSpec("P", bound=int)


def run(func: Callable[P, int]) -> Callable[P, int]: ...
```

**What to do:** keep the declaration.

### Shares a function with a refused one { #feature-type-parameter-modernization-shares-function-with-unconvertible }

A function cannot mix `[...]` type parameters with legacy ones
([PEP 695](https://peps.python.org/pep-0695/#compatibility-with-traditional-typevars)), so a function that uses a
refused declaration keeps all its type parameters legacy.

```python
P = ParamSpec("P", bound=int)
Ts = TypeVarTuple("Ts")


def run(func: Callable[P, tuple[*Ts]]) -> Callable[P, tuple[*Ts]]: ...
```

`P` is reported for its own reason, and `Ts` for this one. Functions that use `Ts` without `P` are still converted.

**What to do:** fix the refused declaration as its section describes, and run the tool again.

### Exported via `__all__` { #feature-type-parameter-modernization-declared-type-parameter-exported }

`T` is in its file's `__all__`, so it is public API. The functions are converted and the declaration stays:

```python
__all__ = ["T", "first"]

T = TypeVar("T")


def first[T](items: list[T]) -> T: ...
```

An imported `T` listed in `__all__` keeps its import. `__all__ += ["T"]` is read too, `__all__.append(...)` is not.

**What to do:** remove `T` from `__all__`, which breaks code that imports it, and run the tool again.

### Only used inside a generic class { #feature-type-parameter-modernization-used-in-generic-class }

Every function using `T` is a method of a class generic over `T`, so there is nothing to convert.

```python
T = TypeVar("T")


class Box(Generic[T]):
    def get(self) -> T: ...
```

A standalone function that also uses `T` is converted, and `T` is then listed both as modified and for review.

**What to do:** run `ruff check --select UP046 --fix --unsafe-fixes` with `target-version` 3.12 or higher, which
rewrites `class Box(Generic[T]):` to `class Box[T]:`, and run the tool again. `UP046` leaves `Protocol[T]` and other
bases alone, so write `class Box[T](MutableSet[T]):` by hand.

### Name not available at module level { #feature-type-parameter-modernization-name-not-at-module-level }

A copied declaration needs every name its arguments use (`bound=Shape`) as the same object in the importing file.
The import stays when the origin binds the name only inside a block, such as `if TYPE_CHECKING:`, or when the
importing file binds it to something else.

```python
# shapes.py
if TYPE_CHECKING:
    from geometry import Shape

T = TypeVar("T", bound="Shape")
```

`shapes.py` is reported too, under *Imported by another project file*.

**What to do:** import the name at module level in the origin, if that causes no import cycle, and run the tool again.
If the importing file has another `Shape`, rename one of the two.

### Origin imports `TypeVar` conditionally { #feature-type-parameter-modernization-origin-imports-constructor-conditionally }

The origin imports `TypeVar` inside an `if` or `try` block. A copy would use the importing file's `TypeVar`, which
may differ at runtime or for the type checker.

```python
# shapes.py
if TYPE_CHECKING:
    from typing_extensions import TypeVar
else:
    from typing import TypeVar

T = TypeVar("T")
```

The importing file keeps its import, and `shapes.py` is reported under *Imported by another project file*.

**What to do:** add the same conditional import to the importing file, then copy the declaration by hand.

### Imported by another project file { #feature-type-parameter-modernization-imported-elsewhere-in-project }

After the run, another file still uses `T` from this module: it reads `shapes.T`, imports `T` under another name, or
keeps `from shapes import T` because localizing was refused or disabled. The functions are converted and the
declaration stays. This is only checked when a directory is passed, and not for an `import *` of this module.

```python
# other.py
import shapes


def last(items: list[shapes.T]) -> shapes.T: ...
```

**What to do:** change the importer to `from shapes import T`, or drop the alias, and run the tool again.

### New name not free { #feature-type-parameter-modernization-new-name-not-free }

Dropping the underscore would clash: the function or class already uses the new name (it reads or assigns `T`, or has
another type parameter `T`), or the new name is not valid (`_class` would become `class`).

```python
def f[_T](x: _T) -> _T:
    return T
```

The type parameter keeps its leading underscore.

**What to do:** rename the other name, or rename the type parameter by hand.

### Use cannot be rewritten { #feature-type-parameter-modernization-use-not-renameable }

A use is written in a form the tool cannot rewrite, such as an annotation split over concatenated strings.

<!-- fmt:off -->

```python
def f[_T](x: "list[" "_T]") -> _T: ...
```

<!-- fmt:on -->

The type parameter keeps its leading underscore.

**What to do:** write the annotation as one string, or without quotes, and run the tool again.

## Related concepts

- [Rewrite semantics](../concepts/rewrite-semantics.md)
- [Type parameters](../concepts/type-parameters.md)

## Verified by test modules

- `test/recipes/test_type_parameter_check.py`
- `test/recipes/test_type_parameter_check_convert.py`
- `test/recipes/test_type_parameter_check_localize.py`
- `test/recipes/test_type_parameter_check_orphaned.py`
- `test/recipes/test_type_parameter_check_properties.py`
- `test/recipes/test_type_parameter_check_variance.py`
- `test/recipes/test_type_parameter_declarations.py`
- `test/recipes/test_type_parameter_localization.py`
- `test/recipes/test_type_parameter_rules.py`
- `test/recipes/test_private_type_parameter_check.py`
- `test/recipes/test_step_runner.py`
- `test/recipes/test_python_refactoring.py`
- `test/utils/test_cst_utils.py`
- `test/utils/test_import_resolution.py`
- `test/utils/test_ruff_utils.py`
- `test/rejuvenation/test_migration_type_recipes.py`

## Implemented by code modules

- [Refactoring recipes](../../developer/modules/recipes.md)
- `src/renaissance/recipes/type_parameter_check.py`, `type_parameter_rules.py`, `type_parameter_declarations.py`,
  `type_parameter_localization.py`, `type_parameter_uses.py`, `private_type_parameter_check.py`, `step_runner.py` and
  `python_refactoring.py`.
- `src/renaissance/utils/import_resolution.py`, `cst_utils.py` and `ruff_utils.py`
- `src/rejuvenation/migration_type_recipes.py` (the CLI)

## API entry points

```shell
python src/rejuvenation/migration_type_recipes.py <path> --py MAJOR.MINOR \
    [--report PATH] [--no-ruff] [--ignore FILE...] [--no-localization]
```

| Argument            | Effect                                                                       |
| ------------------- | ---------------------------------------------------------------------------- |
| `<path>`            | A `.py` file, or a directory scanned recursively                             |
| `--py MAJOR.MINOR`  | Required. The oldest Python version the project supports, 3.12 or higher     |
| `--report PATH`     | Write the Markdown report to `PATH`. Without it, no report is written        |
| `--no-ruff`         | Skip the `ruff` step                                                         |
| `--ignore FILE...`  | Leave these files untouched (see *Shared declaration files*)                 |
| `--no-localization` | Keep every project import of a type parameter (see *Disabling localization*) |

A directory scan skips names starting with `.`, and `__pycache__` and `venv` directories. Files are changed in place,
so run the tool on a clean git checkout.

### The `ruff` step

Unless `--no-ruff` is given, the CLI runs two commands on the modified files:

1. `ruff check --fix --select F401,I001` removes unused imports and sorts the imports.
2. `ruff format` formats the files.

- Both change whole files, including imports and lines the tool did not touch.
- `--select` replaces the project's `select` and `ignore`; its other settings, such as `per-file-ignores` and
  `line-length`, still apply. A project without a `ruff` configuration gets the one of the directory the CLI runs from.
- Without `ruff` in the environment that runs the CLI, the step is silently skipped.

### Output

The CLI prints `File <path> checked.` per file, or `checked again.` when a file is processed again, and then a commit
message if a file was modified. With `--report`, a run where `shapes.py` declares and uses `T`, `main.py` imports it and
`box.py` has `class Box(Generic[T])` writes:

````text
Renaissance TypeParameterCheck migration report
Processed 3 files: 2 modified, 1 need manual review, 0 clean, 0 errors

**TYPE PARAMETERS BY KIND**

| Kind           | Reported | Fixed | Needs review |
| -------------- | -------- | ----- | ------------ |
| `TypeVar`      | 3        | 2     | 1            |
| `ParamSpec`    | 0        | 0     | 0            |
| `TypeVarTuple` | 0        | 0     | 0            |

**UNSAFE REASONS, MOST COMMON FIRST**

| Reason                                           | Count |
| ------------------------------------------------ | ----- |
| only used inside a class that is generic over it | 1     |

**MODIFIED (2)**
  `main.py`
    `T`: import replaced by a local declaration, converted to PEP 695 in functions

  `shapes.py`
    `T`: converted to PEP 695 in functions

**NEEDS MANUAL REVIEW (1)**
  https://tno.github.io/Renaissance.Py/user/features/type-parameter-modernization/

**Only used inside a class that is generic over it**
  `box.py`: `T`

**ERRORS (0)**

**COMMIT MESSAGE**

```text
Convert type parameters to PEP 695 syntax in 2 files (Python 3.12+).

- converted to PEP 695 in functions: T (2 files)
- import replaced by a local declaration: T

1 file left for manual review: only used inside a class that is generic over it (1).
```
````

- Paths are relative to `<path>`. A file can be both modified and in need of review, so the first line can add up to
  more than the total.
- The kinds table counts each name once per file. A name with a reason for review counts as *Needs review*, even when
  it was also converted. The reasons table counts names, and is left out when nothing needs review.
- `MODIFIED` uses four actions: converted to PEP 695 in functions, import replaced by a local declaration, unused
  declaration removed, and leading underscore removed.
- `IGNORED FILES` lists the `--ignore` files, which are not counted as processed. With `--ignore` or
  `--no-localization`, the kinds table gets an `Ignored` column: each name kept imported, once per importing file.
- `COMMIT MESSAGE` is left out when no file was modified. It lists at most ten names per action.

### Exit codes

| Code | Meaning                                                                                               |
| ---- | ----------------------------------------------------------------------------------------------------- |
| 0    | The run completed, also when names need manual review                                                 |
| 1    | The run stopped on an uncaught exception                                                              |
| 2    | Usage error: a missing path, a file that is not `.py`, an invalid `--py` or a missing `--ignore` file |
| 3    | At least one file raised an exception (see `ERRORS`)                                                  |

## Change considerations

See *Extension points* in [Refactoring recipes](../../developer/modules/recipes.md).

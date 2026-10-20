<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Type parameter modernization { #feature-type-parameter-modernization }

**Stable ID:** `FEATURE-TYPE-PARAMETER-MODERNIZATION`

## User-facing summary

Rewrites legacy `TypeVar`, `ParamSpec` and `TypeVarTuple` declarations to [PEP 695](https://peps.python.org/pep-0695/)
syntax in one command. `ruff`'s `UP047` only does part of this, as an unsafe fix: it skips type parameters imported
from another module, `default=` and nested functions, and never removes the old declaration.

```python
# before
T = TypeVar("T")

def first(items: list[T]) -> T: ...

# after
def first[T](items: list[T]) -> T: ...
```

The tool runs three phases:

1. **Localize cross-file imports.** A type parameter imported from another file in the project
   (`from .shapes import T`) is replaced by an exact local copy of its declaration, placed after the file's imports,
   unless the origin is named by `--ignore-localize` (see *Shared declaration files* below).
2. **Convert to PEP 695.** Every function whose signature uses a declared type parameter gets its own `[T]`, with
   bounds, constraints and `default=` carried over (`def f[T: str = str](...)`). `covariant=` and `contravariant=` are
   dropped, since only generic classes have a variance. A nested function gets none when an
   enclosing function's signature uses `T` too. If `T` is also used outside functions (a `Generic[T]` base, an alias),
   the declaration is kept. A function that also uses a type parameter that can't be
   converted is left unchanged.
3. **Remove orphaned declarations.** A module-level `T = TypeVar("T")` that nothing uses is deleted, including one left
   behind by `ruff`'s `UP047` or by a manual rewrite.

## Inputs

A Python file or directory, and the target project's minimum supported Python version (`--py`). Supported
declarations: `TypeVar` (with `bound=`, constraints or `default=`), `ParamSpec` and `TypeVarTuple` (with `default=`).

Imports are resolved against the directory passed to the CLI (the file's own folder for a single file). These are
skipped without a report:

- imports from outside that directory (stdlib, third-party);
- re-exports through an intermediate `__init__.py`, and namespace packages;
- a renamed import (`from .shapes import T as U`); a file whose only type parameters arrive that way counts as clean.

### Shared declaration files { #feature-type-parameter-modernization-ignore-localize }

`--ignore-localize FILE...` names files, relative to `<path>` as the report lists them, whose type parameters are
never copied into the files importing them. Those files keep their imports, so the functions using the imported names
are not converted. Use it for a file that is shared on purpose, such as a `types.py`.

```shell
python src/rejuvenation/migration-type-recipes.py ./some_repo --py 3.12 --ignore-localize pkg/types.py pkg/aliases.py
```

The named files are processed as usual. Give `<path>` first, since the option takes every value after it. A file that
does not exist is a usage error. The report lists the files under `NOT LOCALIZED FROM` and adds an `Ignored` column to
the table, counting each ignored name once per importing file. A file whose only type parameters are ignored counts
as clean.

### Generic classes { #feature-type-parameter-modernization-generic-class }

A class is *generic over* `T` when it declares `T` itself (`class Box[T]:`) or has `T` in a base (`Generic[T]`,
`Protocol[T]`, `Base[int, T]`). Inside such a class, `T` belongs to the class, so the tool never adds `[T]` to its
methods. With `class Box[T]:` the methods don't use the module-level `T`, so a declaration nothing else uses is removed:

```python
# before
T = TypeVar("T")

class Box[T]:
    def get(self) -> T: ...

# after
class Box[T]:
    def get(self) -> T: ...
```

## Outputs / effects

- Every safe change is written to the file in place.
- Every candidate left unchanged for one of the reasons under *Constraints* is listed in the report as **needs manual
  review**, with its reason. The report links this page once, at the top of that section.
- A file listed under `ERRORS` may already be changed: each phase is written before the next one runs, so a failure
  keeps the earlier phases. Check it with `git diff`.

### Known limitations

None of these is a *Constraint*: the tool applies the change. Review the result with `git diff`. Most of them have an
example under *Non-goals* or *Need to fix* in [Refactoring recipes](../../developer/modules/recipes.md#non-goals).

**Can leave code that fails or changes meaning:**

- A decorator or a parameter default that reads `T` (`def f(x: list[T], default=T)`) is not counted as a use, so the
  declaration can be removed and importing the module raises `NameError`.
- A declaration constructed from `from typing import *` is localized without importing `TypeVar`: `NameError`.
- A declaration followed by `;` on the same line is removed without its `;`, leaving invalid syntax. The file is
  reported under `ERRORS`.
- A declaration that breaks the naming rule of PEP 484 (`T = U = TypeVar("T")`, `V = TypeVar("W")`,
  `TypeVar(name)`) gets a wrong rewrite or is skipped with an error.
- `U = TypeVar("U", default=T)` becomes `def f[U = T]`, where `T` still means the module-level one. Fix it by hand as
  `def f[T, U = T]`.
- Only `__all__` marks a declaration as public. One that nothing in the project uses is removed, even if other
  projects import it.
- Only a plain `__all__ = [...]` is read. Annotated (`__all__: list[str] = ...`), `+=`, `.extend()` and `.append()`
  forms are not.
- A `T` used only in the string value of a `TypeAlias` (`A: TypeAlias = "list[T]"`) is seen as unused, so its
  declaration is removed.
- A function that uses a legacy type parameter that stays imported (e.g. from another package) still gets `[...]`
  for the file's own declarations. It then mixes both syntaxes, which type checkers reject.
- A localized `T` is a new object: code comparing type parameters by identity (`is`) sees two different objects.
  A file importing `T` from a localized file gets that copy too.

**Cosmetic or operational:**

- A declaration whose importers are all localized in a run is only removed by a second run.
- Removing a line can leave extra blank lines. Run your formatter afterwards.
- With `--no-ruff`, the imports added by localizing are not merged into the file's existing `from` imports and not
  sorted.
- A modified CRLF file is written back with LF, so `git diff` shows all its lines changed in a repository that stores CRLF.
- The comment lines above a localized declaration are not copied. The comment trailing its line, such as
  `# noqa: PLC0105`, is.
- `Unpack[Ts]` is left as it is. Run `ruff`'s `UP044` to rewrite it to `*Ts` (see
  [Rejected recipes](../../developer/modules/rejected-recipes.md)).
- There is no filtering of files, so a large project can take tens of minutes.

## Constraints

Each case below stops one change and is reported under *needs manual review*.

### Python version gates { #feature-type-parameter-modernization-version-gates }

PEP 695 syntax (`def f[T](...)`) is a `SyntaxError` before Python 3.12, so `--py` (the oldest version the target
supports, not the one running the tool) must be 3.12 or higher. A lower value is a usage error and nothing is
changed. The version is never guessed. Newer syntax is written only when `--py` is new enough:

| Syntax                | PEP                                          | Minimum Python |
| --------------------- | -------------------------------------------- | -------------- |
| `def f[T = int](...)` | [PEP 696](https://peps.python.org/pep-0696/) | 3.13           |

#### PEP 696 version gate { #feature-type-parameter-modernization-pep696-version-gate }

Below 3.13 a declaration with `default=` is not converted, since dropping the default would change what type
checkers infer. Other declarations in the file are still converted, except in functions that also use it (see
*A function also uses a type variable that can't be converted* below).

```python
T = TypeVar("T", default=int)

def first(items: list[T]) -> T: ...
```

With `--py 3.12` the file is unchanged. With `--py 3.13` it becomes `def first[T = int](items: list[T]) -> T: ...`.

**To fix this yourself:** run again with `--py 3.13` if the project supports it. Otherwise keep the declaration.

### A declaration passes an argument with no PEP 695 equivalent { #feature-type-parameter-modernization-no-pep695-equivalent }

The `[...]` syntax cannot write a `bound=` on a `ParamSpec` or `TypeVarTuple`, a `**mapping` of options, or a keyword
added by a later Python version. (`covariant=`, `contravariant=` and `infer_variance=` are fine: a function's type
parameter has no variance.)

```python
P = ParamSpec("P", bound=int)

def run(func: Callable[P, int]) -> Callable[P, int]: ...
```

The file is unchanged.

**To fix this yourself:** keep the declaration.

### A function also uses a type variable that can't be converted { #feature-type-parameter-modernization-shares-function-with-unconvertible }

[PEP 695](https://peps.python.org/pep-0695/#compatibility-with-traditional-typevars) forbids a function from mixing
`[...]` type parameters with legacy ones of its own. A function that uses a
declaration refused for a version gate or an argument with no PEP 695 equivalent keeps all its type parameters
legacy. A legacy type parameter of an enclosing generic class is not the method's own, so it blocks nothing.

```python
P = ParamSpec("P", bound=int)
Ts = TypeVarTuple("Ts")

def run(func: Callable[P, tuple[*Ts]]) -> Callable[P, tuple[*Ts]]: ...
```

The file is unchanged. `P` is reported for its own reason. `Ts` is reported for this one, because every function
using it is left unchanged. Functions that use `Ts` without `P` are still converted.

**To fix this yourself:** fix the refused declaration as its section describes, then run again.

### A declared type parameter is exported via `__all__` { #feature-type-parameter-modernization-declared-type-parameter-exported }

`T` is in its file's plain `__all__ = [...]`, so it is public API. The functions are converted, the declaration is kept.

```python
__all__ = ["T", "first"]

T = TypeVar("T")

def first(items: list[T]) -> T: ...
```

becomes:

```python
__all__ = ["T", "first"]

T = TypeVar("T")

def first[T](items: list[T]) -> T: ...
```

**To remove it yourself:** remove `T` from `__all__` (a breaking change for importers), then delete the declaration.

### A declared type parameter is only used inside a generic class { #feature-type-parameter-modernization-used-in-generic-class }

Only methods of a class with `T` in a base (see *Generic classes* above) use `T`, so there is nothing to
convert. Standalone functions that also use `T` are still converted, and `T` is then listed both as modified and as
needing review, because its declaration stays.

```python
T = TypeVar("T")

class Box(Generic[T]):
    def get(self) -> T: ...
```

The file is unchanged.

**To fix this yourself:** `ruff`'s `UP046` rewrites `Generic[T]` to `class Box[T]:`. Run the tool again afterwards:
it removes the now unused `T = TypeVar("T")`. `UP046` does not touch `Protocol[T]` or a `T` in any other base, so
write `class Box[T](MutableSet[T]):` by hand.

### The declaration uses a name that isn't available at module level { #feature-type-parameter-modernization-name-not-at-module-level }

Localizing copies the declaration into this file, so every name it uses (`bound=Shape`) must be available at module
level, as the same object, in both files. The file is left unchanged when:

- **The origin binds the name only under `if TYPE_CHECKING:`**, or inside a function or class. The copy could not
  import it at runtime.
- **This file binds the name to something else.** It already has a different `Shape`.

```python
# shapes.py
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from geometry import Shape

T = TypeVar("T", bound="Shape")

# main.py
from shapes import T

def biggest(items: list[T]) -> T: ...
```

`main.py` is unchanged and keeps importing `T` from `shapes.py`.

**To fix this yourself:** import the name at module level the same way the origin does, or rename one of the two,
then copy the declaration by hand.

### The origin imports `TypeVar` conditionally { #feature-type-parameter-modernization-origin-imports-constructor-conditionally }

The origin imports `TypeVar` inside an `if` or `try` (for example `typing` or `typing_extensions` per Python
version). A copy would use whatever `TypeVar` this file has, which may fail on some versions.

```python
# shapes.py
try:
    from typing import TypeVar
except ImportError:
    from typing_extensions import TypeVar

T = TypeVar("T")

# main.py
from shapes import T

def first(items: list[T]) -> T: ...
```

`main.py` is unchanged and keeps importing `T` from `shapes.py`.

**To fix this yourself:** add the same conditional import to this file, then copy the declaration by hand.

### A declared type parameter is imported by another project file { #feature-type-parameter-modernization-imported-elsewhere-in-project }

Another file in the target directory imports `T` from this module (`from mod import T` or `mod.T`). The functions
are converted, the declaration is kept. Only checked when a directory is passed; `import *` is not checked.

```python
# shapes.py
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T: ...

# other.py
import shapes

def second(items: list[shapes.T]) -> shapes.T: ...
```

`first` becomes `def first[T](items: list[T]) -> T: ...`. `T = TypeVar("T")` stays, because `other.py` reads
`shapes.T`.

**To remove it yourself:** find that import (`from <module> import <name>` or `<module>.<name>`), remove it, and
run the tool again.

## Related concepts

- [Rewrite semantics](../concepts/rewrite-semantics.md)
- [Type parameters](../concepts/type-parameters.md)

## Verified by test modules

- `test/recipes/test_type_var_check.py`
- `test/recipes/test_type_var_check_convert.py`
- `test/recipes/test_type_var_check_localize.py`
- `test/recipes/test_type_var_check_orphaned.py`
- `test/recipes/test_type_var_check_properties.py`
- `test/recipes/test_type_var_check_variance.py`
- `test/recipes/test_type_var_domain.py`
- `test/recipes/test_step_runner.py`
- `test/recipes/test_python_refactoring.py`
- `test/utils/test_import_resolution.py`
- `test/rejuvenation/test_migration_type_recipes.py`

## Implemented by code modules

- [Refactoring recipes](../../developer/modules/recipes.md)
- `src/renaissance/recipes/type_var_check.py`, `type_var_domain.py`, `step_runner.py` and `python_refactoring.py`.
  The recipe class is still named `TypeVarCheck`.
- `src/renaissance/utils/import_resolution.py`
- `src/rejuvenation/migration-type-recipes.py` (the CLI)

## API entry points

```shell
python src/rejuvenation/migration-type-recipes.py <path> --py MAJOR.MINOR \
    [--report PATH] [--no-ruff] [--ignore-localize FILE...]
```

- `<path>`: a `.py` file or a directory, scanned recursively (`.git`, `__pycache__`, `.venv` and `venv` skipped).
- `--py` (required): the oldest Python version the target project supports, 3.12 or higher.
- `--report`: also write the report to a file.
- `--no-ruff`: skip the final `ruff` pass.
- `--ignore-localize`: files whose type parameters are never copied into the files importing them (see
  *Shared declaration files*).

After the recipe, the CLI runs `ruff check --fix --select F401,I001` on the changed files. This removes **every**
unused import in them, including ones that were unused before (such as `from typing import TypeVar` after the
declaration is gone). It also merges and sorts **every** import block in them, including imports that were unsorted
before, using the `ruff` settings of the project. `ruff` must be installed in the same environment; if it cannot run,
the report still says the pass ran. Files are changed directly, so run it on a git checkout.

The report has a summary line, two summary tables and the sections `MODIFIED`, `NEEDS MANUAL REVIEW` and `ERRORS`.
The tables count the type parameters per kind (`TypeVar`, `ParamSpec`, `TypeVarTuple`) and rank the reasons for manual
review from most to least common. A name counts once per file, as needing review if it has a reason to review. `MODIFIED`
says what was done to each name: converted in functions, import replaced by a local declaration, or unused declaration
removed; a name localized and then removed is listed only as removed. `NEEDS MANUAL REVIEW` gives each name its
reason, and a name can be in both sections. With `--ignore-localize` the report also has the `NOT LOCALIZED FROM`
section and the `Ignored` column. Files are listed relative to `<path>`. Exit codes: 0 when the run completes (manual
review is not a failure), 2 for a usage error, 3 if any file raised an exception.

## Change considerations

See *Extension points* in [Refactoring recipes](../../developer/modules/recipes.md).

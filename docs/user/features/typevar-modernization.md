# TypeVar modernization { #feature-typevar-modernization }

**Stable ID:** `FEATURE-TYPEVAR-MODERNIZATION`

## User-facing summary

Rewrites legacy `TypeVar`, `ParamSpec` and `TypeVarTuple` usage to [PEP 695](https://peps.python.org/pep-0695/)
syntax (`def f[T](...)`) in one command. `ruff`'s `UP047` only does part of this, as an unsafe fix: it skips type
parameters imported from another module, `default=` and nested functions, and never removes the old declaration.
The tool runs three phases:

1. **Localize cross-file imports.** A type parameter imported from another file in the project
   (`from .shapes import T`) is replaced by an exact local copy of its declaration.
2. **Convert to PEP 695.** Every function that uses a declared type parameter gets its own `[T]`, even when several
   functions share it, and also when `T` is used outside functions (a `Generic[T]` base, an alias); the declaration
   is then kept. Bounds, constraints and `default=` are carried over (`def f[T: str = str](...)`).
3. **Remove orphaned declarations.** A module-level `T = TypeVar("T")` that nothing uses anymore is deleted,
   including one left behind by `ruff`'s `UP047` or by a manual rewrite.

Imports left unused (`from typing import TypeVar`) are removed by the CLI's `ruff` pass (see *API entry points*
below). `Unpack[Ts]` is left as it is; run `ruff`'s `UP044` to rewrite it to `*Ts` (see
[Rejected recipes](../../developer/modules/rejected-recipes.md)).

## Inputs

A Python file or directory, and the target project's minimum supported Python version (`--py`). Supported
declarations: `TypeVar` (with `bound=`, constraints or `default=`), `ParamSpec` and `TypeVarTuple` (with `default=`).

Imports are resolved against the directory passed to the CLI (the file's own folder for a single file). These are
skipped without a report:

- imports from outside that directory (stdlib, third-party);
- re-exports through an intermediate `__init__.py`, and namespace packages;
- a renamed import (`from .shapes import T as U`); a file whose only type parameters arrive that way counts as clean.

### Generic classes { #feature-typevar-modernization-generic-class }

A class is *generic over* `T` when it declares `T` itself (`class Box[T]:`) or has `T` in a base (`Generic[T]`,
`Protocol[T]`, `Base[int, T]`). Inside such a class, `T` belongs to the class, so the tool never adds `[T]` to its
methods.

## Outputs / effects

- Every safe change is written to the file in place.
- Every candidate left unchanged for one of the reasons under *Constraints* is listed in the report
  as **needs manual review**, with a link to the section that explains it.

### Known limitations

These cases are **not** reported, so review the changes with `git diff`:

- A multi-line string literal in a converted function, with a line indented less than the body, has its contents
  changed (see [Python AST known limitations](../../developer/modules/python-ast-known-limitations.md)).
- `U = TypeVar("U", default=T)` becomes `def f[U = T]`, where `T` still means the module-level one. Fix it by hand
  as `def f[T, U = T]`.
- A localized `T` is a new object: code comparing type parameters by identity (`is`) sees two different objects.
  A file importing `T` from a localized file gets that copy too.
- A declaration whose importers are all localized in a run is only removed by a second run.
- A `T` used only in string annotations (`def f(x: "T")`) is seen as unused, so its declaration is removed.
- Only a plain `__all__ = [...]` marks `T` as exported. Annotated (`__all__: list[str] = ...`), `+=`, `.extend()`
  and `.append()` forms are not read, so the declaration can be removed.
- Removing a line can leave extra blank lines. Run your formatter afterwards.

## Constraints

Each case below leaves a candidate unchanged and is reported as **unsafe**, with a link to its section.

### Python version gates { #feature-typevar-modernization-version-gates }

PEP 695 syntax is a `SyntaxError` on older Pythons, so the tool only writes it when `--py` (the oldest version the
target supports, not the one running the tool) is new enough. The version is never guessed: unknown counts as too
old. Removing a declaration that is already unused needs no new syntax, so it never depends on `--py`.

| Syntax                | PEP                                          | Minimum Python |
| --------------------- | -------------------------------------------- | -------------- |
| `def f[T](...)`       | [PEP 695](https://peps.python.org/pep-0695/) | 3.12           |
| `def f[T = int](...)` | [PEP 696](https://peps.python.org/pep-0696/) | 3.13           |

#### PEP 695 version gate { #feature-typevar-modernization-pep695-version-gate }

Below 3.12 nothing is converted. Localization and orphan removal still run.

**To fix this yourself:** if the project supports 3.12+, run again with `--py 3.12`. Otherwise keep the old syntax.

#### PEP 696 version gate { #feature-typevar-modernization-pep696-version-gate }

Below 3.13 a declaration with `default=` is not converted, since dropping the default would change what type
checkers infer. Other declarations in the file are still converted.

**To fix this yourself:** run again with `--py 3.13` if the project supports it. Otherwise keep the declaration.

### A declaration passes an argument with no PEP 695 equivalent { #feature-typevar-modernization-no-pep695-equivalent }

The `[...]` syntax cannot write `covariant=`/`contravariant=`, a `bound=` on a `ParamSpec` or `TypeVarTuple`, a
`**mapping` of options, or a keyword added by a later Python version. (`infer_variance=True` is fine: a PEP 695
type parameter always infers its variance.)

**To fix this yourself:** variance only matters for generic classes. If only functions use the type parameter,
remove `covariant=`/`contravariant=` and run again.

### A declared TypeVar is exported via `__all__` { #feature-typevar-modernization-declared-typevar-exported }

`T` is in its file's plain `__all__ = [...]`, so it is public API. The functions are converted, the declaration is kept.

**To remove it yourself:** remove `T` from `__all__` (a breaking change for importers), then delete the declaration.

### A declared TypeVar is only used inside a generic class { #feature-typevar-modernization-used-in-generic-class }

Only methods of a generic class (see *Generic classes* above) use `T`, so there is nothing to
convert. Standalone functions that also use `T` are still converted.

**To fix this yourself:** `ruff`'s `UP046` rewrites `Generic[T]` to `class Box[T]:`. Then delete the unused
`T = TypeVar("T")`.

### A name the declaration uses can't be imported here { #feature-typevar-modernization-declaration-name-unavailable }

Localizing copies the declaration and imports the names it uses (`bound=Shape`) from the origin. That fails when the
origin only imports `Shape` under `if TYPE_CHECKING:`, or when this file already has a different `Shape`.

**To fix this yourself:** import the name the same way the origin does, or rename one of the two, then copy the
declaration by hand.

### The origin imports the TypeVar constructor conditionally { #feature-typevar-modernization-origin-imports-constructor-conditionally }

The origin imports `TypeVar` inside an `if` or `try` (for example `typing` or `typing_extensions` per Python
version). A copy would use whatever `TypeVar` this file has, which may fail on some versions.

**To fix this yourself:** add the same conditional import to this file, then copy the declaration by hand.

### A declared TypeVar is imported by another project file { #feature-typevar-modernization-imported-elsewhere-in-project }

Another file in the target directory imports `T` from this module (`from mod import T` or `mod.T`). The functions
are converted, the declaration is kept. Only checked when a directory is passed; `import *` is not checked.

**To remove it yourself:** find that import (`from <module> import <name>` or `<module>.<name>`), remove it, and
run the tool again.

## Related concepts

- [Rewrite semantics](../concepts/rewrite-semantics.md)

## Verified by test modules

- `test/recipes/test_type_var_check.py`
- `test/recipes/test_type_var_check_convert.py`
- `test/recipes/test_type_var_check_localize.py`
- `test/recipes/test_type_var_check_orphaned.py`
- `test/recipes/test_type_var_check_properties.py`
- `test/recipes/test_type_var_domain.py`
- `test/recipes/test_step_runner.py`
- `test/recipes/test_python_refactoring.py`
- `test/recipes/conftest.py`
- `test/utils/test_unparse_utils.py`
- `test/utils/test_import_resolution.py`
- `test/rejuvenation/test_migration_type_recipes.py`

## Implemented by code modules

- [Refactoring recipes](../../developer/modules/recipes.md)
- `src/renaissance/recipes/type_var_check.py`, `type_var_domain.py`, `step_runner.py` and `python_refactoring.py`
- `src/renaissance/utils/import_resolution.py` and `unparse_utils.py`
- `src/rejuvenation/migration-type-recipes.py` (the CLI)

## API entry points

```shell
python src/rejuvenation/migration-type-recipes.py <path> --py MAJOR.MINOR [--report PATH] [--no-ruff]
```

- `<path>`: a `.py` file or a directory, scanned recursively (`.git`, `__pycache__`, `.venv` and `venv` skipped).
- `--py` (required): the oldest Python version the target project supports.
- `--report`: also write the report to a file.
- `--no-ruff`: skip the final `ruff` pass.

After the recipe, the CLI runs `ruff check --fix --select F401` on the changed files. This removes **every** unused
import in them, including ones that were unused before. `ruff` must be installed in the same environment; if it
cannot run, the report still says the pass ran. Files are changed directly, so run it on a git checkout.

The report has a summary line and the sections `MODIFIED`, `NEEDS MANUAL REVIEW` and `ERRORS`. Exit codes: 0 when
the run completes (manual review is not a failure), 2 for a usage error, 3 if any file raised an exception.

## Change considerations

See *Extension points* in [Refactoring recipes](../../developer/modules/recipes.md).

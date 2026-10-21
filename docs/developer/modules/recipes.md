<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Refactoring recipes

{ #codemod-recipes }

**Stable ID:** `CODEMOD-RECIPES`

## Responsibility

Recipes are `PythonRefactoring` subclasses that rewrite one Python file at a time, for gaps `ruff` does not fully or
safely cover. This page covers `TypeParameterCheck`, the recipe behind
[Type parameter modernization](../../user/features/type-parameter-modernization.md).

## Location

- `src/renaissance/recipes/type_parameter_check.py`: the `TypeParameterCheck` pipeline (orchestration only).
- `src/renaissance/recipes/type_parameter_rules.py`: the refusal rules and the analysis of declarations and their uses.
- `src/renaissance/recipes/step_runner.py`: `Step`/`run_steps`, runs fix actions in order and commits only the ones
  that fixed something.
- `src/renaissance/recipes/python_refactoring.py`: the base class.
- `src/renaissance/utils/import_resolution.py`: the import statements of a module and what they bind, the resolution of
  `from X import Y` to a file in the project, the re-anchoring of one file's relative import on another file, and the
  names each project file imports from the others.
- `src/renaissance/utils/cst_utils.py`: a module's top-level statements and the names they read or bind.

## Public entry points

- `TypeParameterCheck.check()` (and `run()`): runs the three phases through `run_steps`, committing to disk between them.
- The phases, each returning `{name: "fixed" | "unsafe"}` and recording the `UnsafeReason` of each unsafe name:

    | Phase                                                        | Reasons attribute           |
    | ------------------------------------------------------------ | --------------------------- |
    | `localize_imported_typevars()`                               | `cross_file_unsafe_reasons` |
    | `convert_declared_typevars()` (only adds type parameters)    | `converted_unsafe_reasons`  |
    | `remove_orphaned_declarations()` (only removes declarations) | `orphaned_unsafe_reasons`   |

- `type_param_kinds`: maps each type parameter name the phases see to `"TypeVar"`, `"ParamSpec"` or `"TypeVarTuple"`.
- Attributes set by the CLI (`migration-type-recipes.py`): `min_python`, `project_root` (falls back to the file's
  folder), `project_wide_imported_names` (from `collect_project_imported_names`), `ignore_localize_origins` (absolute
  paths of the files `--ignore` names) and `localize_imports` (`False` with `--no-localization`). `ignored_names` holds
  the names this file imports from those files, or all its imported names when `localize_imports` is `False`.
- `PythonRefactoring.process("TypeParameterCheck", file)`, used by `cli.py refactor`, never sets those attributes, so
  `min_python` stays `MIN_SUPPORTED_PYTHON` there and a `default=` declaration is reported `"unsafe"`.

## Internal structure

- **libcst throughout.** The recipe runs on the CST backend (`PythonRefactoring[PythonCstNode]`) and analyses the
  same libcst tree it rewrites; the cross-file phase parses the origin with `libcst.parse_module`. Each edit
  replaces only the node it changes, so formatting and comments elsewhere are kept.

- **Unsafe reasons.** `is_safe_to_remove`, `is_safe_to_localize` and `conversion_refusal` return an `UnsafeReason`
  or `None`. Each of the 8 reasons has an `UnsafeRule` (message + docs anchor) in `UNSAFE_RULES`. The CLI report prints
  each message and links `DOCS_BASE_URL` once.

- **Refusal rules.** Five of the reasons are independent checks, listed as `RefusalRule` entries in
  `CONVERSION_RULES`, `REMOVAL_RULES` and `LOCALIZATION_RULES`; the first rule of a stage that refuses decides the
  reason. The other three (`USED_IN_GENERIC_CLASS`, `SHARES_FUNCTION_WITH_UNCONVERTIBLE`, `NAME_NOT_AT_MODULE_LEVEL`)
  follow from how the phases work and are not listed. Commenting out an entry switches its rule off.
  `NO_PEP695_EQUIVALENT`, `PEP696_VERSION_GATE` and `ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY` then let the recipe write
  code that fails or binds another object; `DECLARED_TYPEVAR_EXPORTED` and `IMPORTED_ELSEWHERE_IN_PROJECT` then let it
  break the files that import the name.

- **Version gates.** `min_python` is never below `MIN_SUPPORTED_PYTHON = (3, 12)`, which the CLI enforces, so PEP 695
  syntax is always available. `conversion_refusal` checks it against `PEP_696_MINIMUM = (3, 13)` for a
  `default=`. A keyword outside `_CONVERTIBLE_KEYWORDS` is refused
  (`NO_PEP695_EQUIVALENT`) instead of dropped. `covariant` and `contravariant` are in the set and are dropped, because
  a function's type parameter has no variance; converting classes would have to refuse them.

- **Uses.** `uses_of` takes a declaration's uses from libcst's scope analysis (`referenced_by`). A use inside a
  string annotation or `cast("T", x)` counts; a `T` that a PEP 695 type parameter of an enclosing function or class
  declares (`def f[T]`, `class C[T]`) does not.

- **Signature edit.** `_add_type_params` replaces only the function's name (`f` → `f[T]`) or, if it has one, its
  type-parameter bracket; the body is never touched. `type_param_text` writes each parameter (`T: int`, `**P`,
  `*Ts`, `= default`) from the declaration's own text.

- **One edit per function.** All type parameters of a function go into one `replace()`, in declaration order, with
  the defaulted ones last (`type_params_bracket`). Two edits on one node would be rejected as conflicting rewrites.
  
- **Owning function.** A legacy type parameter belongs to the function whose signature uses it. `signature_function`
  finds the functions whose parameter or return annotations use the name, and `owning_function` gives each use to the
  outermost of them that encloses it. A nested function whose enclosing function's signature also uses `T` gets no
  `[T]` of its own, since it already sees the outer one. A use outside every such signature, e.g. `y: list[T] = []` in
  a function whose signature doesn't use `T`, is given to no function.

- **Generic classes.** Methods of a class with the name in a base (`generic_classes`) are skipped. A generic class at
  the origin does not block localization.

- **No mixed syntax.** A function using a declaration that `conversion_refusal` rejects gets none of its type
  parameters, since PEP 695 forbids mixing them with legacy ones. A name whose every function is blocked is
  `SHARES_FUNCTION_WITH_UNCONVERTIBLE`. This needs two passes: all refusals are known before any parameter is added.

- **Orphans.** A declaration with no uses left (`uses_of` is empty) is orphaned. Conversion skips such names too.

- **Localization.** The origin's declaration is copied as written, with the comment trailing it when it is alone on
  its line (`declaration_text`). `NAME_NOT_AT_MODULE_LEVEL` if the origin only binds a name its arguments use
  (`declaration_argument_names`) under `if TYPE_CHECKING:` or this file binds it to something else
  (`from_import_sources`). All names localized from one import statement are handled together.

  A name the origin imports, the constructor or one an argument uses, is imported here from the module the origin
  gets it from, with its alias (`from_import_binding`). A relative import of the origin is re-anchored on this file
  by `rebase_relative_module`. A name the origin defines itself, or one whose module this file can't name, is
  imported from the origin.

- **Imports.** An import whose names are now declared locally is narrowed, keeping its comments, or dropped with its
  trailing comment when no name remains. The needed imports, each once per file, and then the declarations go after
  the file's last import, so no import is left below code (E402). A localization is written where its import was
  when that import shares its line with other statements and is dropped, when no import of the file remains, or when
  a statement between it and the last import reads one of its names. Merging and sorting the added imports, and
  removing imports that became unused, is left to the CLI's `ruff check --fix --select F401,I001` pass.

- **Line endings.** Files are read with universal newlines and a modified file is written back with LF, also on the
  lines the recipe did not change. A file the recipe does not modify is not rewritten.

## Related features

- [Type parameter modernization](../../user/features/type-parameter-modernization.md)

## Related concepts

- [Rewrite semantics](../../user/concepts/rewrite-semantics.md)
- [Python version gates](../../user/features/type-parameter-modernization.md#feature-type-parameter-modernization-version-gates)

## Validated by test modules

See *Verified by test modules* in [Type parameter modernization](../../user/features/type-parameter-modernization.md).

## Extension points

- A new recipe is a `PythonRefactoring` subclass in its own `snake_case`-named module in `src/renaissance/recipes/`;
  no registration is needed.
- A new type-parameter-declaring construct: extend `_is_type_param_call` and `type_param_text` together.
- A keyword added by a later Python, or future PEP 695 syntax for variance or a bound on `**P`/`*Ts`: add it to
  `_CONVERTIBLE_KEYWORDS` and carry it over in `type_param_text`.
- A new refusal rule: add a check function and a `RefusalRule` entry to the stage's tuple in `type_parameter_rules.py`,
  a message and anchor to `UNSAFE_RULES`, and a section to the feature page.
- A new version gate uses the syntax's own minimum Python from its PEP, not a value copied from another gate.
- Re-exports through `__init__.py` or namespace packages (PEP 420): extend `resolve_project_module`.
- `Step`/`run_steps` is generic and can be reused by any recipe.
- `Step`/`run_steps` is generic and can be reused by any recipe.

## Non-goals

- Make the tool more efficient. Currently the tool does not make use of any filtering or similar features, making it
  exponentially slower than other tools (Ruff can run on milliseconds on big projects, while it may take upwards of 30
  minutes per project with this tool). This is a limitation of it, and a low priority fix due to time constraints.

- The target's minimum Python is not detected (e.g. from `requires-python`); it must be passed with `--py`. A
  project with:

    ```toml
    [project]
    requires-python = ">=3.13"
    ```

    run with `--py 3.12` is treated as below 3.13, so a `default=` declaration is not converted.

- Re-exports, namespace packages, `import *` and renamed imports are not followed. In:

    ```python
    # origin.py
    from typing import TypeVar

    T = TypeVar("T")

    # main.py
    from origin import T as U

    def first(items: list[U]) -> U: ...
    ```

    `main.py` is left unchanged.

- Only declarations in the file itself can block a function. A legacy type parameter that stays imported, such as one
  from another package, does not. In:

    ```python
    from other_package import K

    V = TypeVar("V")

    def get(mapping: dict[K, V], key: K) -> V: ...
    ```

    `get` becomes `def get[V](mapping: dict[K, V], key: K) -> V: ...`. `K` is still the imported legacy type
    parameter, so `get` mixes both syntaxes, which
    [PEP 695](https://peps.python.org/pep-0695/#compatibility-with-traditional-typevars) forbids. Type checkers
    report an error.

- Imported names are collected once before the run, so removing a declaration whose importers were all localized
  needs a second run, which `--second-pass` does for the files concerned. With `origin.py` as above and:

    ```python
    # main.py
    from origin import T

    def first(items: list[T]) -> T: ...
    ```

    the first run turns `main.py` into `def first[T](items: list[T]) -> T: ...`, but keeps `T` in `origin.py`, since
    `main.py` imported it when the run started. A second run removes it.

- Only a plain `__all__ = [...]` is read to detect an exported declaration. In:

    ```python
    __all__: list[str] = ["T", "first"]

    T = TypeVar("T")

    def first(items: list[T]) -> T: ...
    ```

    `first` is converted and `T = TypeVar("T")` is removed, although `__all__` exports it.

- A declaration is only treated as public API when `__all__` lists it, since the tool sees nothing outside the scanned
  project. One that nothing in the project uses is removed, even if other projects import it. `--ignore` leaves
  such a file untouched. In:

    ```python
    # mylib/typing.py
    from typing import TypeVar

    KeyT = TypeVar("KeyT", bytes, str)
    ```

    `KeyT = TypeVar("KeyT", bytes, str)` is removed, so `from mylib.typing import KeyT` fails elsewhere. With
    `__all__ = ["KeyT"]` it is kept.

- A name used only in the string value of a `TypeAlias` is not seen as a use, so its declaration can be removed as
  orphaned. In:

    ```python
    T = TypeVar("T")
    Pairs: TypeAlias = "list[tuple[T, T]]"
    ```

    `T = TypeVar("T")` is removed, and `Pairs` refers to an undefined `T`.

- `Unpack[Ts]` → `*Ts` is left to `ruff`'s `UP044`, see [Rejected recipes](rejected-recipes.md). In:

    ```python
    Ts = TypeVarTuple("Ts")

    def pack(*args: Unpack[Ts]) -> tuple[Unpack[Ts]]: ...
    ```

    only `[*Ts]` is added: `def pack[*Ts](*args: Unpack[Ts]) -> tuple[Unpack[Ts]]: ...`.

- An import that follows another statement on the same line is written back wrongly. This is rare, and `ruff`'s
  `E702` flags such lines. In:

    ```python
    import os; from origin import T
    ```

    the lines that replace the import get an extra indent, a syntax error.

- Without the CLI's `ruff` pass (`--no-ruff`, or using the recipe as a library) the added imports are not merged
  into the file's existing `from` imports and not sorted. They are still placed with the other imports.

- A declaration still read by a decorator or a parameter default of a converted function can be removed. This is
  rare. In:

    ```python
    T = TypeVar("T")

    def first(items: list[T], default=T) -> T: ...
    ```

    `first` becomes `def first[T](items: list[T], default=T) -> T: ...`. The annotations now use the new type
    parameter, but `default=T` is evaluated outside it and still reads the module-level `T`. libcst places it inside
    the type parameter's scope, so the declaration looks unused and is removed: importing the module raises
    `NameError`.

- A declaration followed by `;` on the same line is removed without its `;`. This is rare, and `ruff`'s `E702` flags
  such lines. In:

    ```python
    T = TypeVar("T"); U = 1

    def first(items: list[T]) -> T: ...
    ```

    the file is written as `; U = 1`, a syntax error, and reported under errors.

- Declarations that break the naming rule of [PEP 484](https://peps.python.org/pep-0484/) (a single variable named
  after the string argument) are not handled. This is rare, and `ruff`'s `PLC0132` flags a mismatched name:

    ```python
    T = U = TypeVar("T")  # if T is unused, the statement is removed and U is no longer defined
    V = TypeVar("W")      # def f(x: V) -> V becomes def f[W](x: V) -> V
    X = TypeVar(name)     # AttributeError: no phase is applied to the file
    ```

- A declaration whose constructor comes from `from typing import *` is localized without importing it. This is rare,
  and `ruff`'s `F403` flags the star import. In:

    ```python
    # origin.py
    from typing import *

    T = TypeVar("T")

    # main.py
    from origin import T

    class Pair(dict[str, T]): ...
    ```

    `main.py` gets `T = TypeVar("T")` without an import of `TypeVar`, so it raises `NameError`.

- A `default=` that uses another declaration is carried over as is. This is rare. With `--py 3.13`:

    ```python
    T = TypeVar("T")
    U = TypeVar("U", default=T)

    def first(items: list[U]) -> U: ...
    ```

    becomes `def first[U = T](items: list[U]) -> U: ...`, whose default still refers to the module-level `T`.

- A constructor written with its module, such as `typing.TypeVar`, is not recognised. This is rare. In:

    ```python
    T = typing.TypeVar("T")

    def first(items: list[T]) -> T: ...
    ```

    `first` is left unchanged and the file is reported clean.

- Absolute imports are resolved from the given path, so in a `src/` layout run on the repository root,
  `from pkg.typing import T` does not find `src/pkg/typing.py`. This is rare. In:

    ```python
    # src/pkg/typing.py
    T = TypeVar("T")

    # src/pkg/other.py
    from pkg.typing import T

    def first(items: list[T]) -> T: ...
    ```

    `T = TypeVar("T")` is removed and `other.py` fails with `ImportError`.

## Need to fix

Errors that should be fixed, not accepted.

- The comment lines above a localized declaration are not copied. Only the comment trailing its line is, because
  the rewriter handles a comment as one line
  ([issue 189](https://github.com/TNO/Renaissance.Py/issues/189)). In:

    ```python
    # origin.py
    from typing import TypeVar

    # Placeholder until the array API types are narrower.
    T = TypeVar("T")  # noqa: PLC0105

    # main.py
    from origin import T
    ```

    `main.py` gets `T = TypeVar("T")  # noqa: PLC0105` without the comment above it. The origin keeps its comment
    when it drops the declaration.

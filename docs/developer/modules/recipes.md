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
safely cover. This page covers `TypeParameterCheck` and `PrivateTypeParameterCheck`, the recipes behind
[Type parameter modernization](../../user/features/type-parameter-modernization.md). That page describes what they
change and refuse; this page says where it is decided.

## Location

- `src/renaissance/recipes/type_parameter_check.py`: the `TypeParameterCheck` pipeline and the edits its phases write.
- `src/renaissance/recipes/type_parameter_rules.py`: the reasons a type parameter is left unconverted, and the refusal
  rules.
- `src/renaissance/recipes/type_parameter_declarations.py`: reads and rewrites a declaration (`T = TypeVar(...)`).
- `src/renaissance/recipes/type_parameter_localization.py`: decides which imported type parameters get a local
  declaration, and the imports and text that replace them.
- `src/renaissance/recipes/type_parameter_uses.py`: finds where a declared name is used.
- `src/renaissance/recipes/private_type_parameter_check.py`: `PrivateTypeParameterCheck`, which drops the leading
  underscore from the type parameters of functions and classes and from every use they bind.
- `src/renaissance/recipes/step_runner.py`: `Step`/`run_steps`, runs fix actions in order and commits only the ones
  that fixed something.
- `src/renaissance/recipes/python_refactoring.py`: the base class. `typed_root` gives the root node as the recipe's node
  class.
- `src/renaissance/utils/import_resolution.py`: the import statements of a module and what they bind, the resolution of
  `from X import Y` to a project file, the re-anchoring of a relative import on another file, and `ProjectImportGraph`,
  the names each project file imports from the others.
- `src/renaissance/utils/cst_utils.py`: a module's top-level statements, the names they read or bind and the comment
  trailing a statement's line.
- `src/renaissance/utils/ruff_utils.py`: `run_ruff_import_cleanup` (`ruff check --fix --select F401,I001`) and
  `run_ruff_format` (`ruff format`), which the CLI runs on the changed files.
- `src/rejuvenation/migration_type_recipes.py`: the CLI. It sets the recipe attributes, orders and repeats the files
  with `ProjectImportGraph`, runs the `ruff` step and writes the report.

## Public entry points

- `TypeParameterCheck.check()` (and `run()`) runs the three phases through `run_steps`, committing to disk between
  them. Each phase returns `{name: "fixed" | "unsafe"}` and records the `UnsafeReason` of each unsafe name:

    | Phase                            | Step label   | Reasons attribute           |
    | -------------------------------- | ------------ | --------------------------- |
    | `localize_imported_typevars()`   | `cross_file` | `cross_file_unsafe_reasons` |
    | `convert_declared_typevars()`    | `converted`  | `converted_unsafe_reasons`  |
    | `remove_orphaned_declarations()` | `orphaned`   | `orphaned_unsafe_reasons`   |

    `converted_unsafe_reasons` can also hold a fixed name that a generic class still uses (`USED_IN_GENERIC_CLASS`).
- `type_param_kinds` maps each type parameter name the phases see to `"TypeVar"`, `"ParamSpec"` or `"TypeVarTuple"`.
- The CLI sets these attributes before `check()`:

    | Attribute                     | Value                                                                       |
    | ----------------------------- | --------------------------------------------------------------------------- |
    | `min_python`                  | `--py`                                                                      |
    | `project_root`                | `<path>`, or the file's folder for a single file                            |
    | `project_wide_imported_names` | `ProjectImportGraph.imported_names` of the file                             |
    | `ignore_localize_origins`     | the absolute paths of the `--ignore` files                                  |
    | `localize_imports`            | `False` with `--no-localization`                                            |

    `ignored_names` then holds the names this file imports from those files, or from any project file when
    `localize_imports` is `False`.
- `PythonRefactoring.process("TypeParameterCheck", file)`, used by `cli.py refactor`, sets none of these attributes.
  `min_python` stays `MIN_SUPPORTED_PYTHON`, so a `default=` is refused, and `project_wide_imported_names` stays empty,
  so a declaration that other files import is removed.
- `PrivateTypeParameterCheck.check()` (and `run()`) renames each private type parameter and returns
  `{old name: "fixed" | "unsafe"}`. A name refused in any declaration is `"unsafe"`. `unsafe_reasons` holds the reason
  of each unsafe name, and `type_param_kinds` the kind of each name. The CLI runs it after `TypeParameterCheck`, as
  step `renamed`.

## Internal structure

### Common

- Both recipes use the CST backend (`PythonRefactoring[PythonCstNode]`) and read the tree through `typed_root`. Each
  edit replaces only the node it changes, so formatting and comments elsewhere are kept.
- `uses_of` takes a declaration's uses from libcst's scope analysis (`referenced_by`). A use inside a string annotation
  or `cast("T", x)` counts. A `T` that a PEP 695 type parameter of an enclosing function or class declares does not.
- Files are read with universal newlines, and a modified file is written back with LF, also on the lines the recipe did
  not change. A file the recipe does not modify is not rewritten.

### Refusals

`is_safe_to_remove`, `is_safe_to_localize` and `conversion_refusal` return an `UnsafeReason` or `None`. Each reason has
a message in `UNSAFE_RULES`, which the report prints; the report links `DOCS_BASE_URL` once.

| Reason                                     | Decided by                                |
| ------------------------------------------ | ----------------------------------------- |
| `NO_PEP695_EQUIVALENT`                     | `CONVERSION_RULES`                        |
| `PEP696_VERSION_GATE`                      | `CONVERSION_RULES`                        |
| `DECLARED_TYPEVAR_EXPORTED`                | `REMOVAL_RULES`                           |
| `IMPORTED_ELSEWHERE_IN_PROJECT`            | `REMOVAL_RULES`                           |
| `ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY` | `LOCALIZATION_RULES`                      |
| `SHARES_FUNCTION_WITH_UNCONVERTIBLE`       | `convert_declared_typevars`               |
| `USED_IN_GENERIC_CLASS`                    | `convert_declared_typevars`               |
| `NAME_NOT_AT_MODULE_LEVEL`                 | `plan_localizations`                      |
| `NEW_NAME_NOT_FREE`                        | `PrivateTypeParameterCheck._plan_renames` |
| `USE_NOT_RENAMEABLE`                       | `PrivateTypeParameterCheck._plan_renames` |

In a rules tuple, the first rule that refuses decides the reason. Commenting out an entry switches its rule off, after
which the recipe can write code that fails or breaks the files that import the name.

### Conversion

- The CLI rejects `--py` below `MIN_SUPPORTED_PYTHON = (3, 12)`; the recipe itself does not check it.
  `conversion_refusal` compares `min_python` with `PEP_696_MINIMUM = (3, 13)` for a `default=`.
- A keyword outside `_CONVERTIBLE_KEYWORDS` is refused (`NO_PEP695_EQUIVALENT`) instead of dropped. `covariant` and
  `contravariant` (on `TypeVar` and `ParamSpec`) and `infer_variance` are dropped, because a function's type parameter
  has no variance. Converting classes would have to refuse them.
- A legacy type parameter belongs to the function whose signature uses it. `signature_function` finds the functions
  whose parameter or return annotations use the name, and `owning_function` gives each use to the outermost of them.
  A use outside every such signature, such as `y: list[T] = []` in a function whose signature does not use `T`, goes
  to no function.
- Functions inside a class with the name in a base (`generic_classes`) are skipped.
- A function using a declaration that `conversion_refusal` rejects gets none of its type parameters, since PEP 695
  forbids mixing them with legacy ones. All refusals are therefore collected (`_plan_conversions`) before any
  parameter is added.
- `_add_type_params` replaces only the function's name (`f` → `f[T]`) or its existing bracket, never the body. All type
  parameters of a function go into one `replace()`, in declaration order with the defaulted ones last
  (`type_params_bracket`), since two edits on one node conflict. `type_param_text` writes each parameter (`T: int`,
  `**P`, `*Ts`, `= default`) from the declaration's own text.

### Removal

A declaration with no uses left (`uses_of` is empty) is orphaned and removed, unless `REMOVAL_RULES` refuses.
Conversion skips orphaned names too.

### Localization

- The origin is parsed with `libcst.parse_module`, and its declaration is copied as written, with the comment trailing
  it when it is alone on its line (`declaration_text`). All names localized from one import statement are handled
  together.
- `NAME_NOT_AT_MODULE_LEVEL` is returned when the origin binds a name the arguments use (`declaration_argument_names`)
  only inside a block, or this file binds it to something else (`from_import_sources`).
- A name the origin imports, such as the constructor, is imported here from the same module, with its alias
  (`from_import_binding`). `rebase_relative_module` re-anchors a relative import of the origin on this file. A name the
  origin defines itself, or one whose module this file cannot name, is imported from the origin.
- The import a localization replaces is this file's binding, so `is_safe_to_remove` checks it too. Only
  `DECLARED_TYPEVAR_EXPORTED` can refuse there, since the planner gets no `project_wide_imported_names`.
- An import whose names are now declared locally is narrowed, keeping its comments, or dropped with its trailing
  comment. The needed imports, once each, and then the declarations go after the last import that stays, so no import
  ends up below code (E402). If every import is dropped, they replace the last dropped import line (`_anchor_index`).
  They go where the replaced import was when it is dropped from a line with other statements, or when a statement
  between it and the last import reads one of its names. Merging, sorting and removing unused imports is left to the
  CLI's `ruff` step.

### Processing order

The CLI reads the imports of every file, `--ignore` files included, into a `ProjectImportGraph`. It processes origins
before the files importing from them (`processing_order`); the files of an import cycle form one group. After each
file, the graph reads its imports again, and a file is processed again (`_merge_reports`) while the names the project
imports from it change. A re-export through `pkg/__init__.py` is localized there first, so its importers copy it from
that file.

### Private type parameters

`PrivateTypeParameterCheck` finds the type parameters of every `def`, `async def` and `class`, nested ones included,
with `_DECLARATION_PATTERNS` on an RST parse of the same text. It maps each one to its libcst node by offset and takes
its uses from `referenced_by`, so a module-level `_T` of the same name is left alone. A name inside a string annotation
is renamed inside the string. `NEW_NAME_NOT_FREE` refuses a new name that is not a valid identifier (`_`, `_1`), is
already a name in the function or class, or would appear twice in its bracket. `USE_NOT_RENAMEABLE` refuses a use that
is neither a name nor a single string.

## Related features

- [Type parameter modernization](../../user/features/type-parameter-modernization.md)

## Related concepts

- [Type parameters](../../user/concepts/type-parameters.md)
- [Rewrite semantics](../../user/concepts/rewrite-semantics.md)
- [Python version gates](../../user/features/type-parameter-modernization.md#feature-type-parameter-modernization-version-gates)

## Validated by test modules

See *Verified by test modules* in [Type parameter modernization](../../user/features/type-parameter-modernization.md).

## Extension points

- A new recipe is a `PythonRefactoring` subclass in a module named after the class in `snake_case`, in
  `src/renaissance/recipes/`. `cli.py refactor` finds it by name. A CST recipe subclasses
  `PythonRefactoring[PythonCstNode]` and reads the tree through `typed_root`.
- A new declaring constructor: add it to `_CONSTRUCTORS` and `_CONVERTIBLE_KEYWORDS`, and write its syntax in
  `type_param_text`, all in `type_parameter_declarations.py`.
- A keyword added by a later Python, or future PEP 695 syntax for variance or a bound on `**P`/`*Ts`: add it to
  `_CONVERTIBLE_KEYWORDS` and carry it over in `type_param_text`.
- A new refusal rule: add an `UnsafeReason` member, a check function, a `RefusalRule` entry in the stage's tuple and
  an `UnsafeRule` message in `UNSAFE_RULES`, all in `type_parameter_rules.py`, and a section on the feature page.
- A new version gate compares `min_python` with a constant holding the minimum Python from the syntax's own PEP, as
  `PEP_696_MINIMUM` does.
- A namespace package ([PEP 420](https://peps.python.org/pep-0420/)) as an import's origin: extend
  `resolve_project_module`.
- `Step`/`run_steps` is generic and can be reused by any recipe.

## Non-goals

The feature page shows what each case does to the user's code, mostly under *Known limitations*.

- Every file is parsed and analysed, with no caching. An origin is parsed once per importing statement, and a file is
  processed again while the names imported from it change.
- The target's minimum Python is not read from `requires-python`; `--py` sets `min_python`.
- Renamed imports (`from shapes import T as U`) and imports inside blocks are not localized (`_Planner.run` reads only
  top-level `from` imports).
- A file importing with `from origin import *` is not an importer: `imported_project_names` records `"*"`, so the
  origin's declaration is removed once the origin itself no longer uses it.
- Only declarations in the file can block a function. A legacy type parameter that stays imported, such as
  `typing.AnyStr`, does not, so the function mixes both syntaxes.
- `__all__.extend(...)` and `__all__.append(...)` are not read by `_is_exported`.
- Only `__all__` marks a declaration as public. One that nothing in the project uses is removed, even if other
  projects import it; `--ignore` keeps such a file.
- A name used only in the string value of a `TypeAlias` is not a use for `uses_of`, so its declaration is removed.
- `Unpack[Ts]` → `*Ts` is left to `ruff`'s `UP044`, see [Rejected recipes](rejected-recipes.md).
- A statement on the same line as a removed declaration or a replaced import (`T = TypeVar("T"); x = 1`) is written
  back wrongly, a syntax error. `ruff`'s `E702` flags such lines.
- Without the `ruff` step (`--no-ruff`, or the recipe used as a library), the added imports are not merged or sorted.
- A decorator or a parameter default that reads `T` is evaluated outside the new type parameter's scope, but libcst
  places it inside, so the declaration looks unused and is removed.
- Declarations that break the naming rule of [PEP 484](https://peps.python.org/pep-0484/) (`T = U = TypeVar("T")`,
  `V = TypeVar("W")`, `TypeVar(name)`) are not handled. `ruff`'s `PLC0132` flags a mismatched name.
- A constructor from `from typing import *` is not imported with the copy (`ctor_source is None`).
- A `default=` that names another declaration is carried over as is, so `def f[U = T]` can still mean the module-level
  `T`.
- A constructor written with its module (`typing.TypeVar`) is not recognised by `_is_type_param_call`.
- Absolute imports are resolved from `<path>`, so in a `src/` layout run on the repository root, `from pkg.shapes import
  T` does not find `src/pkg/shapes.py`.

## Need to fix

Temporary list of defects the code should fix, with their issue where one exists. Each entry moves out once it is
fixed or accepted as a non-goal.

- The comment lines above a localized declaration are not copied, because the rewriter handles a comment as one line
  ([issue 189](https://github.com/TNO/Renaissance.Py/issues/189)).
- An existing type parameter bracket on a converted function is rebuilt on one line, losing its comments and line
  breaks (`_add_type_params`, [issue 279](https://github.com/TNO/Renaissance.Py/issues/279)).
- A localized declaration whose constructor this file already imports from another module adds a second import that
  shadows the first ([issue 279](https://github.com/TNO/Renaissance.Py/issues/279)).
- A file that starts with a UTF-8 byte order mark is corrupted: `def identity(x: T) -> T:` becomes
  `def ideidentity[T] T) -> T:` ([issue 153](https://github.com/TNO/Renaissance.Py/issues/153)).
- A file that is not valid UTF-8 stops the whole run with an uncaught `UnicodeDecodeError` (exit code 1), because
  `imported_project_names` does not catch it. It should be listed under `ERRORS`
  ([issue 188](https://github.com/TNO/Renaissance.Py/issues/188)).
- `PrivateTypeParameterCheck.check()` marks a name `"unsafe"` for the whole file when one declaration of it is
  refused. `def ok[_T]` then keeps its underscore because another function's `_T` is refused, unless another name in
  the file is renamed: `run_steps` commits every planned edit, and `ok` is renamed while the report lists `_T` only for
  review.
- `--report` to a directory that does not exist raises `FileNotFoundError` after the files were rewritten, so the run
  exits with code 1 and the report is lost.
- The `ruff` step runs in the CLI's working directory and hides its output (`ruff_utils.py`). A project without a
  `ruff` configuration gets the one of that directory, and a missing or failing `ruff` gives no message.
- `_report_generic_class_leftovers` adds `USED_IN_GENERIC_CLASS` to a name that was converted in a standalone function,
  so the message "only used inside a class that is generic over it" is wrong there.
- Without `--report`, a run whose only outcome is refusals prints nothing about them, since the commit message is only
  printed when a file was modified.
- Type parameters of a `type` statement (`type A[_T] = list[_T]`) are neither renamed nor reported.
- `T = U = TypeVar("T")` leaves `U` undefined, and `V = TypeVar("W")` writes `def f[W](x: V) -> V`, both without a
  warning.
- The report prints the `UNSAFE_RULES` messages as raw Markdown, so `__all__` renders as bold "all" and `**mapping`
  breaks the bold heading. It also writes "1 files" and "1 errors", and the reasons table counts names where the
  commit message counts files.

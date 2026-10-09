# Refactoring recipes

{ #codemod-recipes }

**Stable ID:** `CODEMOD-RECIPES`

## Responsibility

Recipes are `PythonRefactoring` subclasses that rewrite one Python file at a time, for gaps `ruff` does not fully or
safely cover. This page covers `TypeVarCheck`, the recipe behind
[TypeVar modernization](../../user/features/typevar-modernization.md).

## Location

- `src/renaissance/recipes/type_var_check.py`: the `TypeVarCheck` pipeline (orchestration only).
- `src/renaissance/recipes/type_var_domain.py`: domain model and safety analysis.
- `src/renaissance/recipes/step_runner.py`: `Step`/`run_steps`, runs fix actions in order and commits only the ones
  that fixed something.
- `src/renaissance/recipes/python_refactoring.py`: the base class, with `find_rst_node`.
- `src/renaissance/utils/unparse_utils.py`: `unparse_signature_only`, adds the type-parameter bracket to a signature.
- `src/renaissance/utils/import_resolution.py`: resolves `from X import Y` to a file in the project, and re-anchors
  one file's relative import on another file.

## Public entry points

- `TypeVarCheck.check()` (and `run()`): runs the three phases through `run_steps`, committing to disk between them.
- The phases, each returning `{name: "fixed" | "unsafe"}` and recording the `UnsafeReason` of each unsafe name:

    | Phase                                                        | Reasons attribute           |
    | ------------------------------------------------------------ | --------------------------- |
    | `localize_imported_typevars()`                               | `cross_file_unsafe_reasons` |
    | `convert_declared_typevars()` (only adds type parameters)    | `converted_unsafe_reasons`  |
    | `remove_orphaned_declarations()` (only removes declarations) | `orphaned_unsafe_reasons`   |

- Attributes set by the CLI (`migration-type-recipes.py`): `min_python`, `project_root` (falls back to the file's
  folder) and `project_wide_imported_names` (from `collect_project_imported_names`).
- `PythonRefactoring.process("TypeVarCheck", file)`, used by `cli.py refactor`, never sets those attributes, so every
  version-gated rewrite is reported `"unsafe"` there.

## Internal structure

- **Plain `ast`.** The recipe uses `ast.walk`/`ast.unparse` instead of RstNode traversal, since the cross-file phase
  parses a second file with `ast.parse()` anyway.
- **Unsafe reasons.** `is_safe_to_remove`/`is_safe_to_localize` and `_conversion_refusal` return an `UnsafeReason`
  or `None`. Each of the 8 reasons has an `UnsafeRule` (message + docs anchor) in `UNSAFE_RULES`; `doc_link()` turns
  it into the URL that the CLI report prints.
- **Version gates.** `_conversion_refusal` checks `min_python` against `PEP_695_MINIMUM = (3, 12)` and, for a
  `default=`, `PEP_696_MINIMUM = (3, 13)`. `None` never passes. A keyword outside `_CONVERTIBLE_KEYWORDS` is refused
  (`NO_PEP695_EQUIVALENT`) instead of dropped.
- **Signature splice.** `unparse_signature_only` inserts only the `[T]`/`[**P]`/`[*Ts]` bracket into the function's
  original text, so comments and formatting survive (`ast.unparse` would lose them). It does re-indent the function,
  see [Python AST known limitations](python-ast-known-limitations.md).
- **One edit per function.** All type parameters of a function go into one `replace()`, in declaration order, then
  `type_params_defaults_last`. Two edits on one node would be rejected as conflicting rewrites.
- **Outermost function.** `functions_using_nodes` gives a name to the outermost function using it, never to a nested
  closure, which already sees the outer `[T]`.
- **Generic classes.** Methods of a class generic over the name (`functions_in_generic_classes`, via
  `_declares_type_param`/`_inherits_type_param`) are skipped. A generic class at the origin does not block
  localization.
- **Orphans.** `all_refs_shadowed_by_pep695` reports a declaration dead when every reference sits inside a function
  whose own type parameters declare the same name. Conversion uses it too, to skip names that need no work.
- **Localization.** The origin's declaration is copied with `ast.unparse`, and the names its arguments use
  (`declaration_argument_names`) are imported from the origin. `DECLARATION_NAME_UNAVAILABLE` if the origin only
  binds a name under `if TYPE_CHECKING:` or this file binds it to something else (`from_import_sources`). All
  names localized from one import statement go into one `replace()`, with each needed import added once. A
  constructor the origin imports relatively is re-anchored on this file by `rebase_relative_module`, or imported
  from the origin itself when that is not possible.
- **Imports.** An import whose names are now declared locally is narrowed with `ast.unparse`, or replaced by the
  declarations when no name remains. Removing imports that became unused is left to the CLI's `ruff check --fix --select F401` pass.

## Related features

- [TypeVar modernization](../../user/features/typevar-modernization.md)

## Related concepts

- [Rewrite semantics](../../user/concepts/rewrite-semantics.md)
- [Python version gates](../../user/features/typevar-modernization.md#feature-typevar-modernization-version-gates)

## Validated by test modules

See *Verified by test modules* in [TypeVar modernization](../../user/features/typevar-modernization.md).

## Extension points

- A new recipe is a `PythonRefactoring` subclass in its own `snake_case`-named module in `src/renaissance/recipes/`;
  no registration is needed.
- A new type-parameter-declaring construct: extend `_is_type_param_call` and `build_type_param` together.
- A keyword added by a later Python, or future PEP 695 syntax for variance or a bound on `**P`/`*Ts`: add it to
  `_CONVERTIBLE_KEYWORDS` and carry it over in `build_type_param`.
- A new version gate uses the syntax's own minimum Python from its PEP, not a value copied from another gate.
- Re-exports through `__init__.py` or namespace packages (PEP 420): extend `resolve_project_module`.
- `find_rst_node`, `unparse_signature_only` and `Step`/`run_steps` are generic and can be reused by any recipe.

## Non-goals

- The target's minimum Python is not detected (e.g. from `requires-python`); it must be passed with `--py`.
- Re-exports, namespace packages, `import *` and renamed imports (`from .origin import T as U`) are not followed.
- Imported names are collected once before the run, so removing a declaration whose importers were all localized
  needs a second run.
- Only a plain `__all__ = [...]` is read to detect an exported declaration.
- `Unpack[Ts]` → `*Ts` is left to `ruff`'s `UP044`, see [Rejected recipes](rejected-recipes.md).
- Known bugs, tracked as `xfail` tests:
    - `test_does_not_convert_default_referencing_another_declaration` (`test_type_var_check_convert.py`)
    - `test_converts_function_preserving_multiline_string_literal` (`test_type_var_check_convert.py`)
    - `test_keeps_declaration_used_in_a_string_annotation` (`test_type_var_check_orphaned.py`)
    - `test_narrowing_an_import_keeps_its_comments` (`test_type_var_check_localize.py`)

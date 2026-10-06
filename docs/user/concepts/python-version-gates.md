# Python version gates

{ #concept-python-version-gates }

**Stable ID:** `CONCEPT-PYTHON-VERSION-GATES`

## Purpose

Explains the mechanism every version-gated recipe shares for deciding whether a rewrite is safe to apply: take
the target codebase's minimum supported Python version as given by the user, and only rewrite when that minimum
meets the specific syntax feature's own threshold - never a guess.

## Scope

Applies to any recipe whose rewrite introduces syntax that doesn't exist on every supported Python version. One
recipe uses this today:

| Feature | PEP | Minimum Python | Recipe |
| --- | --- | --- | --- |
| Generic type-parameter syntax (`def f[T](...)`) | [PEP 695](https://peps.python.org/pep-0695/) | 3.12 | [TypeVar modernization](../features/typevar-modernization.md) (`TypeVarCheck`) |

## Definition

Each version-gated recipe has a `min_python` attribute (`tuple[int, int] | None`, default `None`) holding the
target codebase's minimum supported Python version. The tool never detects it: `migration-type-recipes.py`
requires it through its `--py MAJOR.MINOR` flag and sets it on every recipe it runs; tests set it directly.

A gate (`TypeVarCheck._target_supports_pep695()`) returns `True` only if `min_python` is set *and* meets the
feature's own threshold (`PEP_695_MINIMUM = (3, 12)`).

## Invariants / guarantees

- **Conservative by design.** An unknown `min_python` (a recipe run without it being set) and a minimum below
  the threshold both produce the same result: `False`. An unknown minimum is never treated as safe - the syntax
  a gate protects is a hard `SyntaxError` on an older interpreter, so guessing wrong isn't a cosmetic mistake,
  it's a codebase the recipe would break outright. For example, with `--py 3.11` the CLI reports the PEP 695
  conversion `"unsafe"`; with `--py 3.12` it converts. See
  [TypeVar modernization](../features/typevar-modernization.md)'s Constraints section.
- The gate protects rewrites that *introduce* new syntax. Removing a declaration that is already dead, because
  every use of it is shadowed by a PEP 695 type parameter, adds no syntax and does not depend on `min_python`.

## Related features

- [TypeVar modernization](../features/typevar-modernization.md)

## Related tests

- `test/recipes/test_type_var_check_convert.py` (`test_version_gate_below_pep695_reports_unsafe_with_reason`)
- `test/rejuvenation/test_migration_type_recipes.py` (`test_py_flag_gates_rewrites`)

## Related code

- `rejuvenation/migration-type-recipes.py` (the `--py` flag)
- `renaissance/recipes/type_var_check.py` (`min_python`, `_target_supports_pep695`, `PEP_695_MINIMUM`)

## Notes

The threshold a recipe picks is the *syntax feature's own* true minimum, not an arbitrary stricter value chosen
to match another recipe for consistency. A future version-gated recipe should find the PEP's real minimum and
gate there, rather than defaulting to whatever an existing recipe already uses.

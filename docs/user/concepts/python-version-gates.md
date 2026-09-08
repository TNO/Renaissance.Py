# Python version gates

{ #concept-python-version-gates }

**Stable ID:** `CONCEPT-PYTHON-VERSION-GATES`

## Purpose

Explains the mechanism every version-gated recipe shares for deciding whether a rewrite is safe to apply: find
the target codebase's minimum declared Python version, and only rewrite when that minimum meets the specific
syntax feature's own threshold - never a guess.

## Scope

Applies to any recipe whose rewrite introduces syntax that doesn't exist on every supported Python version. Two
recipes use this today:

| Feature | PEP | Minimum Python | Recipe |
| --- | --- | --- | --- |
| Generic type-parameter syntax (`def f[T](...)`) | [PEP 695](https://peps.python.org/pep-0695/) | 3.12 | [TypeVar modernization](../features/typevar-modernization.md) (`TypeVarCheck`) |
| Native `*Ts` star-unpacking for `TypeVarTuple` | [PEP 646](https://peps.python.org/pep-0646/) | 3.11 | [TypeVar modernization](../features/typevar-modernization.md) (`TypeVarTupleCheck`) |

## Definition

Each gate is a small `target_supports_<pep>(file_path)` function (`type_var_check.py`'s `target_supports_pep695`,
`type_var_tuple_check.py`'s `target_supports_pep646`) that:

1. Calls `renaissance.utils.python_version.minimum_python_version(file_path)`, which finds the nearest
   `pyproject.toml` above `file_path` and parses its `requires-python` specifier down to the lowest version it
   allows.
2. Compares that minimum against the feature's own threshold (`PEP_695_MINIMUM = (3, 12)` /
   `PEP_646_MINIMUM = (3, 11)`).
3. Returns `True` only if a minimum was found *and* it meets the threshold.

A recipe instance can also set `min_python_override` directly (a class attribute, e.g. `recipe.min_python_override
= (3, 12)`) to skip the `pyproject.toml` lookup entirely - used by tests, and by `migration-type-recipes.py`'s
`--min-python MAJOR.MINOR` flag to let a user override the detected minimum from the CLI.

## Invariants / guarantees

- **Conservative by design.** No `pyproject.toml`, a missing or unparsable `requires-python`, or a minimum below
  the threshold all produce the same result: `False`. An unknown minimum is never treated as safe - the syntax
  each of these gates protects is a hard `SyntaxError` on an older interpreter, so guessing wrong isn't a
  cosmetic mistake, it's a codebase the recipe would break outright.
- Two recipes can use two different thresholds independently and correctly in the same CLI run, each compared
  against its own true minimum - see [TypeVar modernization](../features/typevar-modernization.md)'s Constraints
  section for the concrete case (a target declaring exactly 3.11 fixes `Unpack[T]` → `*T` but still reports PEP
  695 conversion `"unsafe"`).

## Related features

- [TypeVar modernization](../features/typevar-modernization.md)

## Related code

- `renaissance/utils/python_version.py` (`minimum_python_version`, `KNOWN_PYTHON_VERSIONS`)
- `renaissance/recipes/type_var_check.py` (`target_supports_pep695`, `PEP_695_MINIMUM`)
- `renaissance/recipes/type_var_tuple_check.py` (`target_supports_pep646`, `PEP_646_MINIMUM`)

## Notes

The threshold a recipe picks is the *syntax feature's own* true minimum, not an arbitrary stricter value chosen
to match another recipe for consistency - `TypeVarTupleCheck` gates at 3.11, one version below `TypeVarCheck`'s
3.12, precisely because that's what PEP 646 actually requires. A future version-gated recipe should do the same:
find the PEP's real minimum and gate there, rather than defaulting to whatever an existing recipe already uses.

# Python version gates

{ #concept-python-version-gates }

**Stable ID:** `CONCEPT-PYTHON-VERSION-GATES`

## Purpose

Explains the mechanism every version-gated recipe shares for deciding whether a rewrite is safe to apply: take
the target codebase's minimum supported Python version as given by the user, and only rewrite when that minimum
meets the specific syntax feature's own threshold - never a guess.

## Scope

Applies to any recipe whose rewrite introduces syntax that doesn't exist on every supported Python version. Two
recipes use this today:

| Feature | PEP | Minimum Python | Recipe |
| --- | --- | --- | --- |
| Generic type-parameter syntax (`def f[T](...)`) | [PEP 695](https://peps.python.org/pep-0695/) | 3.12 | [TypeVar modernization](../features/typevar-modernization.md) (`TypeVarCheck`) |
| Native `*Ts` star-unpacking for `TypeVarTuple` | [PEP 646](https://peps.python.org/pep-0646/) | 3.11 | [TypeVar modernization](../features/typevar-modernization.md) (`TypeVarTupleCheck`) |

## Definition

Each version-gated recipe has a `min_python` attribute (`tuple[int, int] | None`, default `None`) holding the
target codebase's minimum supported Python version. The tool never detects it: `migration-type-recipes.py`
requires it through its `--py MAJOR.MINOR` flag and sets it on every recipe it runs; tests set it directly.

Each gate (`TypeVarCheck._target_supports_pep695()`, `TypeVarTupleCheck._target_supports_pep646()`) returns
`True` only if `min_python` is set *and* meets the feature's own threshold (`PEP_695_MINIMUM = (3, 12)` /
`PEP_646_MINIMUM = (3, 11)`).

## Invariants / guarantees

- **Conservative by design.** An unknown `min_python` (a recipe run without it being set) and a minimum below
  the threshold both produce the same result: `False`. An unknown minimum is never treated as safe - the syntax
  each of these gates protects is a hard `SyntaxError` on an older interpreter, so guessing wrong isn't a
  cosmetic mistake, it's a codebase the recipe would break outright.
- Two recipes can use two different thresholds independently and correctly in the same CLI run, each compared
  against its own true minimum - see [TypeVar modernization](../features/typevar-modernization.md)'s Constraints
  section for the concrete case (a target declaring exactly 3.11 fixes `Unpack[T]` → `*T` but still reports PEP
  695 conversion `"unsafe"`).

## Related features

- [TypeVar modernization](../features/typevar-modernization.md)

## Related code

- `rejuvenation/migration-type-recipes.py` (the `--py` flag)
- `renaissance/recipes/type_var_check.py` (`min_python`, `_target_supports_pep695`, `PEP_695_MINIMUM`)
- `renaissance/recipes/type_var_tuple_check.py` (`min_python`, `_target_supports_pep646`, `PEP_646_MINIMUM`)

## Notes

The threshold a recipe picks is the *syntax feature's own* true minimum, not an arbitrary stricter value chosen
to match another recipe for consistency - `TypeVarTupleCheck` gates at 3.11, one version below `TypeVarCheck`'s
3.12, precisely because that's what PEP 646 actually requires. A future version-gated recipe should do the same:
find the PEP's real minimum and gate there, rather than defaulting to whatever an existing recipe already uses.

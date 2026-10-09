# Rejected recipes

{ #codemod-rejected-recipes }

**Stable ID:** `CODEMOD-REJECTED-RECIPES`

## Responsibility

Recipes that were built and later removed because an existing tool already covers them. Check that the reason still
holds before rebuilding one.

## TypeVarTupleCheck (`Unpack[T]` → `*T`)

{ #codemod-rejected-recipes-typevartuplecheck }

**What it did:** rewrote `Unpack[Ts]` to `*Ts` ([PEP 646](https://peps.python.org/pep-0646/), Python 3.11+) for a
`TypeVarTuple` declared in the same file.

**Why it was removed:**

- `ruff`'s `UP044` covers more cases (`typing.Unpack`, imported `TypeVarTuple`s, `Unpack[tuple[...]]`) and skips
  places where `*` is invalid, where the recipe wrote a `SyntaxError`.
- Its only advantage was not needing `--unsafe-fixes`.
- Legacy `Unpack[...]` is rare in real projects.

**What to use instead**, after [TypeVar modernization](../../user/features/typevar-modernization.md) (which converts
the `TypeVarTuple` declaration but leaves `Unpack[Ts]` as it is):

```shell
ruff check --select UP044 --unsafe-fixes --target-version py311 --fix <path>
```

Use `py311` or higher, and review any `Unpack[tuple[...]]` rewrite: unlike `Unpack[Ts]`, it changes the runtime
object.

## Related features

- [TypeVar modernization](../../user/features/typevar-modernization.md)

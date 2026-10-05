# Rejected recipes

{ #codemod-rejected-recipes }

**Stable ID:** `CODEMOD-REJECTED-RECIPES`

## Responsibility

Records recipes that were built and later removed because an existing tool already covers them, and what to use
instead. A recipe listed here should not be rebuilt without first checking that the reason for removing it no
longer holds.

## TypeVarTupleCheck (`Unpack[T]` → `*T`)

{ #codemod-rejected-recipes-typevartuplecheck }

**What it did:** rewrote a legacy `Unpack[Ts]` usage to native `*Ts` syntax
([PEP 646](https://peps.python.org/pep-0646/), Python 3.11+), for a `TypeVarTuple` declared at module level in
the same file.

**Why it was removed:**

- `ruff`'s `UP044` rule (`non-pep646-unpack`) covers every case the recipe handled, and more: `typing.Unpack[...]`,
  a `TypeVarTuple` imported from another module, and `Unpack[tuple[...]]`. It also leaves `Unpack` in place
  where `*` is not valid syntax (a plain parameter, `**kwargs: Unpack[SomeTypedDict]`), whereas the recipe
  rewrote `x: Unpack[Ts]` into a `SyntaxError`.
- The only thing the recipe added was not needing `--unsafe-fixes`. `ruff` marks the fix unsafe because
  `Unpack[tuple[...]]` and `*tuple[...]` are different objects at runtime; for a `TypeVarTuple` both forms are
  identical.
- Legacy `Unpack[...]` usage is rare in real projects, so the recipe added little value to the CLI.

**What to use instead:**

```shell
ruff check --select UP044 --unsafe-fixes --target-version py311 --fix <path>
```

`--target-version` must be `py311` or higher. Review the diff for any `Unpack[tuple[...]]` rewrite before
keeping it.

**Interaction with [TypeVar modernization](../../user/features/typevar-modernization.md):** `TypeVarCheck` still
converts a `TypeVarTuple`'s declaration, including one imported from another file in the target project, to
`def f[*Ts](...)`, and leaves its `Unpack[Ts]` usages as they are. Run `UP044` afterwards to rewrite those.

## Related features

- [TypeVar modernization](../../user/features/typevar-modernization.md)

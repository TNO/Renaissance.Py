# Type parameter scope

{ #concept-type-parameter-scope }

**Stable ID:** `CONCEPT-TYPE-PARAMETER-SCOPE`

## Purpose

Explains why a `TypeVar`, `ParamSpec`, or `TypeVarTuple` declaration behaves differently depending on how many
functions in a file use it, and why that distinction matters for rewriting it to
[PEP 695](https://peps.python.org/pep-0695/) generic syntax safely - even though the
[TypeVar modernization](../features/typevar-modernization.md) recipe itself converts both cases the same way.

## Scope

Applies to legacy-style type parameter declarations (`T = TypeVar("T")` and its `ParamSpec`/`TypeVarTuple`
siblings) declared at module level in Python source, and to the
[TypeVar modernization](../features/typevar-modernization.md) recipe that rewrites them.

## Definition

A type parameter declared at module level is **single-scope** if exactly one function (or method) in the file
references it, and **multi-scope** if two or more functions reference it.

- A single-scope declaration can be converted to PEP 695 syntax (`def f[T](x: T) -> T:`) in isolation: the
  declaration is deleted and `T` moves into that one function's signature.
- A multi-scope declaration requires every referencing function to be converted together, because each converted
  function gets its own independently-scoped `T` — the shared module-level declaration only becomes safe to
  delete once none of its use sites still need it. A tool that looks at one function at a time can convert each
  use site, but can never safely confirm that *every* use site has been converted, so it cannot delete the
  declaration without risking a `NameError` in a use site it has not seen yet.

## Invariants / guarantees

A type parameter - single-scope or multi-scope alike - is only safe to convert (with its declaration removed) when:

- it is not listed in the module's `__all__`, and
- it is not referenced anywhere outside a function body — for example as a `Generic[T]` base of a class, or in a
  module-level type alias.

If either holds, the name is reported as unsafe to convert instead. These checks apply regardless of scope; scope
only changes *why* the declaration can't simply be deleted once every use site is converted - not whether the
`__all__`/outside-use checks apply.

## Related features

- [TypeVar modernization](../features/typevar-modernization.md)

## Related tests

- `test/refactoring/test_type_var_check.py`

## Related code

- `src/renaissance/refactoring/type_var_check.py`

## Notes

`ruff`'s `UP047` rule can convert a single-scope type parameter safely, but only as an unsafe fix
(`--unsafe-fixes`), and even then never removes the now-redundant declaration. For a multi-scope type parameter
it's worse: `ruff` evaluates one function at a time and has no single pass that sees every use site at once, so it
can convert each function's signature individually but can never safely decide the declaration is fully dead.
Seeing every use site at once, within one file, is what lets a whole-file recipe finish the conversion (and delete
the declaration) safely for both cases in one pass - which is why
[TypeVar modernization](../features/typevar-modernization.md) doesn't special-case single-scope: the same safety
check and the same rewrite apply either way.

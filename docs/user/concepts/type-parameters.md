<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Type parameters

{ #concept-type-parameters }

**Stable ID:** `CONCEPT-TYPE-PARAMETERS`

## Purpose

Fixes the meaning of three terms that are easy to confuse: *type hint*, *type parameter* and *type variable*.

## Scope

The terms as used by [Type parameter modernization](../features/type-parameter-modernization.md). This page does not describe
how the tool rewrites them.

## Definition

A **type hint** states the type of a value. A **type parameter** is a type left open in a generic function, class or
type alias. A **type variable** is the kind of type parameter that stands for one type.

```python
def first[T](items: list[T]) -> T: ...
```

| Part of the code      | Term           | Role                                |
| --------------------- | -------------- | ----------------------------------- |
| ``[T]``               | Type parameter | Declares ``T``, a type left open    |
| ``items: list[T]``    | Type hint      | States the type of ``items``        |
| ``T`` after the arrow | Type hint      | States the type of the return value |

Here `T` is a type variable.

Before Python 3.12, `T` had to be declared separately. The legacy form still works on every version:

```python
T = TypeVar("T")

def first(items: list[T]) -> T: ...
```

Three kinds of type parameter exist:

| Kind of type parameter  | Written as | Legacy declaration |
| ----------------------- | ---------- | ------------------ |
| Type variable           | ``T``      | ``TypeVar``        |
| Type variable tuple     | ``*Ts``    | ``TypeVarTuple``   |
| Parameter specification | ``**P``    | ``ParamSpec``      |

## Invariants / guarantees

1. A type hint is never a type parameter: `list[T]` is a type hint, `T` is the type parameter it uses.
2. The legacy and the PEP 695 declaration define the same kind of type parameter. Only the place where it is declared
   differs, and the inline form needs Python 3.12.

## Related features

- [Type parameter modernization](../features/type-parameter-modernization.md)

## Notes

- A PEP 695 type parameter is also a `TypeVar`, `TypeVarTuple` or `ParamSpec` object at runtime (see
  `__type_params__`). This is why "TypeVar" is often used for all three kinds.
- The documentation says *type parameter* for the general case and *type variable* only for the single-type kind.
- The recipe class is still named `TypeVarCheck`.

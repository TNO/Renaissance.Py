import ast
import keyword
import string

from itertools import islice
from typing import Sequence
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy, composite, DrawFn

# ============================================================
# Private AST builders (module-local, as requested)
# ============================================================


def _build_name(id_: str) -> ast.Name:
    return ast.Name(id=id_, ctx=ast.Load())


def _build_subscript(value: ast.expr, slice_expr: ast.expr) -> ast.Subscript:
    return ast.Subscript(value=value, slice=slice_expr, ctx=ast.Load())


def _build_tuple(elts: list[ast.expr]) -> ast.Tuple:
    return ast.Tuple(elts=elts, ctx=ast.Load())


def _build_list(elts: list[ast.expr]) -> ast.List:
    return ast.List(elts=elts, ctx=ast.Load())


def _build_dict(keys: Sequence[ast.expr], values: list[ast.expr]) -> ast.Dict:
    return ast.Dict(keys=list(keys), values=values)


def _build_bitor_chain(exprs: list[ast.expr]) -> ast.expr:
    """Build A | B | C as (A | B) | C. Requires at least one element."""
    if not exprs:
        raise ValueError("_build_bitor_chain() requires at least one expression")
    acc = exprs[0]
    for e in islice(
        exprs, 1, None
    ):  # iterates exprs[1:] but without creating a new list
        acc = ast.BinOp(left=acc, op=ast.BitOr(), right=e)
    return acc


def _build_tuple_type_slice(type_args: list[ast.expr]) -> ast.expr:
    """
    Build the slice part of `tuple[...]`.
    - For non-empty list: tuple[T1, T2, ...]  -> slice = (T1, T2, ...)
    - For empty list    : tuple[()]           -> slice = ((),)  i.e., a 1-tuple containing the empty tuple
    """
    return (
        _build_tuple([_build_tuple([])]) if not type_args else _build_tuple(type_args)
    )


# -------------------- depth sizing -------------------------


def max_len(depth: int) -> int:
    """Max length/arity/arms as function of depth."""
    return 3 * depth


# ============================================================
# Base types and their AST Constant value strategies
# ============================================================

BASE_VALUES: dict[str, SearchStrategy[ast.expr]] = {
    "bool": st.builds(ast.Constant, st.booleans()),
    "int": st.builds(ast.Constant, st.integers(min_value=-1000, max_value=1000)),
    "str": st.builds(ast.Constant, st.text(min_size=0, max_size=5)),
    "float": st.builds(
        ast.Constant, st.floats(allow_nan=False, allow_infinity=False, width=32)
    ),
    "bytes": st.builds(ast.Constant, st.binary(min_size=0, max_size=5)),
}
BASE_TYPE: SearchStrategy[str] = st.sampled_from(list(BASE_VALUES.keys()))


def base_pair() -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
    """(type_expr, value_gen) for scalar base types."""
    return BASE_TYPE.map(lambda t: (_build_name(t), BASE_VALUES[t]))


# -------------------- PUBLIC constructors: list/tuple/union/dict --------------------
# Each takes a child strategy and current depth.


@composite
def gen_list(
    draw: DrawFn,
    child: SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]],
    depth: int,
) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    t, vg = draw(child)
    return (
        _build_subscript(_build_name("list"), t),
        st.lists(vg, min_size=0, max_size=max_len(depth)).map(_build_list),
    )


@composite
def gen_union(
    draw: DrawFn,
    child: SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]],
    depth: int,
) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    members = draw(st.lists(child, min_size=2, max_size=max_len(depth)))
    type_exprs = [t for (t, _vg) in members]
    value_gens = [vg for (_t, vg) in members]
    return _build_bitor_chain(type_exprs), st.one_of(*value_gens)


@composite
def gen_dict(
    draw: DrawFn,
    child: SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]],
    depth: int,
) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    # keys restricted to base types to keep runtime values hashable
    kname = draw(BASE_TYPE)
    kt, kvg = _build_name(kname), BASE_VALUES[kname]

    vt, vvg = draw(child)
    t = _build_subscript(_build_name("dict"), _build_tuple([kt, vt]))

    pairs = draw(st.lists(st.tuples(kvg, vvg), min_size=0, max_size=max_len(depth)))
    keys = [k for (k, _v) in pairs]
    vals = [v for (_k, v) in pairs]
    return t, st.just(_build_dict(keys, vals))


@composite
def gen_tuple(
    draw: DrawFn,
    child: SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]],
    depth: int,
) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    members = draw(st.lists(child, min_size=0, max_size=max_len(depth)))
    if not members:
        t = _build_subscript(_build_name("tuple"), _build_tuple_type_slice([]))
        return t, st.just(_build_tuple([]))
    type_exprs = [t for (t, _vg) in members]
    value_gens = [vg for (_t, vg) in members]
    t = _build_subscript(_build_name("tuple"), _build_tuple_type_slice(type_exprs))
    return t, st.tuples(*value_gens).map(lambda xs: _build_tuple(list(xs)))


# -------------------- recursive dispatchers (public) --------------------


def type_and_value(
    depth: int,
) -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
    """Full recursive mix: base | list | tuple | union | dict."""
    if depth <= 0:
        return base_pair()
    depth = depth - 1
    child = type_and_value(depth)
    return st.one_of(
        base_pair(),
        gen_list(child, depth),
        gen_tuple(child, depth),
        gen_union(child, depth),
        gen_dict(child, depth),
    )


def union_type_and_value(
    depth: int,
) -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
    """Focused: unions only (plus base leaves for recursion/shrinking)."""
    if depth <= 0:
        return base_pair()
    child = union_type_and_value(depth - 1)
    return st.one_of(base_pair(), gen_union(child, depth))


def list_type_and_value(
    depth: int,
) -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
    return st.just( gen_list(, depth-1))
    if depth <= 0:
        return base_pair()
    child = list_type_and_value(depth - 1)
    return st.one_of(base_pair(), gen_list(child, depth))


def tuple_type_and_value(
    depth: int,
) -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
    if depth <= 0:
        return base_pair()
    child = tuple_type_and_value(depth - 1)
    return st.one_of(base_pair(), gen_tuple(child, depth))


def dict_type_and_value(
    depth: int,
) -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
    if depth <= 0:
        return base_pair()
    child = dict_type_and_value(depth - 1)
    return st.one_of(base_pair(), gen_dict(child, depth))


# -------------------- arguments generator (unchanged API, uses tv injection) --------------------

_FIRST: SearchStrategy[str] = st.sampled_from(string.ascii_letters + "_")
_REST: SearchStrategy[str] = st.text(
    string.ascii_letters + string.digits + "_", min_size=0, max_size=20
)
IDENTIFIER: SearchStrategy[str] = st.builds(str.__add__, _FIRST, _REST).filter(
    lambda s: not keyword.iskeyword(s)
)


def _make_arg(name: str, ann: ast.expr | None) -> ast.arg:
    return ast.arg(arg=name, annotation=ann)


def _bernoulli(p: float) -> st.SearchStrategy[bool]:
    return st.integers(0, 999).map(lambda x: x < int(p * 1000))


@composite
def arguments_from_types(
    draw: DrawFn,
    *,
    depth: int = 2,
    tv: SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]] | None = None,
    max_posonly: int = 2,
    max_args: int = 3,
    max_kwonly: int = 3,
    p_annot: float = 0.5,
    p_kwonly_default: float = 0.5,
) -> ast.arguments:
    tv = type_and_value(depth) if tv is None else tv

    n_pos = draw(st.integers(0, max_posonly))
    n_args = draw(st.integers(0, max_args))
    n_kw = draw(st.integers(0, max_kwonly))
    use_vararg = draw(st.booleans())
    use_kwarg = draw(st.booleans())

    total = n_pos + n_args + n_kw + use_vararg + use_kwarg
    names = draw(st.lists(IDENTIFIER, min_size=total, max_size=total, unique=True))
    it = iter(names)

    # positional params
    total_pos = n_pos + n_args
    n_def = draw(st.integers(0, total_pos))
    tail_start = total_pos - n_def

    anns: list[ast.expr | None] = [None] * total_pos
    defaults: list[ast.expr] = []

    for i in range(total_pos):
        if i >= tail_start:
            both = draw(st.booleans())
            t, vg = draw(tv)
            if both:
                anns[i] = t
            defaults.append(draw(vg))
        else:
            if draw(_bernoulli(p_annot)):
                t, _vg = draw(tv)
                anns[i] = t

    posonlyargs = [_make_arg(next(it), anns[i]) for i in range(n_pos)]
    args = [_make_arg(next(it), anns[n_pos + j]) for j in range(n_args)]

    # kw-only params
    kwonlyargs: list[ast.arg] = []
    kw_defaults: list[ast.expr | None] = []
    for _ in range(n_kw):
        name = next(it)
        do_ann = draw(_bernoulli(p_annot))
        do_def = draw(_bernoulli(p_kwonly_default))
        if do_ann and do_def:
            t, vg = draw(tv)
            kwonlyargs.append(_make_arg(name, t))
            kw_defaults.append(draw(vg))
        elif do_ann:
            t, _vg = draw(tv)
            kwonlyargs.append(_make_arg(name, t))
            kw_defaults.append(None)
        elif do_def:
            _t, vg = draw(tv)
            kwonlyargs.append(_make_arg(name, None))
            kw_defaults.append(draw(vg))
        else:
            kwonlyargs.append(_make_arg(name, None))
            kw_defaults.append(None)

    # vararg/kwarg
    vararg = None
    if use_vararg:
        name = next(it)
        ann = draw(tv)[0] if draw(_bernoulli(p_annot)) else None
        vararg = _make_arg(name, ann)

    kwarg = None
    if use_kwarg:
        name = next(it)
        ann = draw(tv)[0] if draw(_bernoulli(p_annot)) else None
        kwarg = _make_arg(name, ann)

    return ast.arguments(
        posonlyargs=posonlyargs,
        args=args,
        vararg=vararg,
        kwonlyargs=kwonlyargs,
        kw_defaults=kw_defaults,
        kwarg=kwarg,
        defaults=defaults,
    )

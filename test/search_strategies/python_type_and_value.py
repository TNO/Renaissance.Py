import ast
import keyword
import string
from itertools import islice

from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, SearchStrategy, composite

DEFAULT_DEPTH: int = 3

# -------------------- policy --------------------


def max_len(depth: int) -> int:
    return 3 * depth


# -------------------- AST builders (private) --------------------


def _build_name(id_: str) -> ast.Name:
    return ast.Name(id=id_, ctx=ast.Load())


def _build_subscript(value: ast.expr, slice_expr: ast.expr) -> ast.Subscript:
    return ast.Subscript(value=value, slice=slice_expr, ctx=ast.Load())


def _build_list(elts: list[ast.expr]) -> ast.List:
    return ast.List(elts=elts, ctx=ast.Load())


def _build_dict(keys: list[ast.expr], values: list[ast.expr]) -> ast.Dict:
    # ast.Dict.keys is list[expr | None]; list is invariant, so copy keys for type correctness
    return ast.Dict(keys=list(keys), values=values)


def _build_tuple(elts: list[ast.expr]) -> ast.Tuple:
    return ast.Tuple(elts=elts, ctx=ast.Load())


def _build_tuple_type_slice(type_args: list[ast.expr]) -> ast.expr:
    # tuple[()] uses slice == ((),)
    return _build_tuple([_build_tuple([])]) if not type_args else _build_tuple(type_args)


def _build_bitor_chain(exprs: list[ast.expr]) -> ast.expr:
    if len(exprs) < 2:
        raise ValueError("union requires at least two arms")
    acc = exprs[0]
    for e in islice(exprs, 1, None):  # avoids slice copy
        acc = ast.BinOp(left=acc, op=ast.BitOr(), right=e)
    return acc


def _build_arg(name: str, ann: ast.expr | None) -> ast.arg:
    return ast.arg(arg=name, annotation=ann, type_comment=None)


# -------------------- base types --------------------

BASE_VALUES: dict[str, SearchStrategy[ast.expr]] = {
    "NoneType": st.just(ast.Constant(None)),
    "bool": st.builds(ast.Constant, st.booleans()),
    "int": st.builds(ast.Constant, st.integers(min_value=-1000, max_value=1000)),
    "str": st.builds(ast.Constant, st.text(min_size=0, max_size=5)),
    "float": st.builds(ast.Constant, st.floats(allow_nan=False, allow_infinity=False, width=32)),
    "bytes": st.builds(ast.Constant, st.binary(min_size=0, max_size=5)),
}
BASE_TYPE: SearchStrategy[str] = st.sampled_from(list(BASE_VALUES))


# ============================================================
# Generator family (PUBLIC): gen_base/gen_list/gen_dict/gen_union/gen_type
# All return: (type_expr: ast.expr, value_gen: SearchStrategy[ast.expr])
# ============================================================


@composite
def gen_base(draw: DrawFn) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    tname = draw(BASE_TYPE)
    return _build_name(tname), BASE_VALUES[tname]


@composite
def gen_list(draw: DrawFn, depth: int = DEFAULT_DEPTH) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    elem_t, elem_vg = draw(gen_type(depth - 1))
    return (
        _build_subscript(_build_name("list"), elem_t),
        st.lists(elem_vg, min_size=0, max_size=max_len(depth)).map(_build_list),
    )


@composite
def gen_dict(draw: DrawFn, depth: int = DEFAULT_DEPTH) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    # keys restricted to base types for runtime hashability
    kname = draw(BASE_TYPE)
    kt, kvg = _build_name(kname), BASE_VALUES[kname]

    vt, vvg = draw(gen_type(depth - 1))
    type_expr = _build_subscript(_build_name("dict"), _build_tuple([kt, vt]))

    value_gen = st.lists(
        st.tuples(kvg, vvg),
        min_size=0,
        max_size=max_len(depth),
    ).map(lambda pairs: _build_dict([k for (k, _v) in pairs], [v for (_k, v) in pairs]))

    return type_expr, value_gen


@composite
def gen_union(draw: DrawFn, depth: int = DEFAULT_DEPTH) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    members = draw(
        st.lists(
            gen_type(depth - 1),
            min_size=2,
            max_size=2 if depth <= 1 else max_len(depth),
        )
    )

    ts = [t for (t, _vg) in members]
    vgs = [vg for (_t, vg) in members]
    return _build_bitor_chain(ts), st.one_of(*vgs)


@composite
def gen_tuple(draw: DrawFn, depth: int = DEFAULT_DEPTH) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    members = draw(st.lists(gen_type(depth - 1), min_size=0, max_size=max_len(depth)))
    if not members:
        t = _build_subscript(_build_name("tuple"), _build_tuple_type_slice([]))  # tuple[()]
        return t, st.just(_build_tuple([]))  # ()
    ts = [t for (t, _vg) in members]
    vgs = [vg for (_t, vg) in members]
    t = _build_subscript(_build_name("tuple"), _build_tuple_type_slice(ts))
    return t, st.tuples(*vgs).map(lambda xs: _build_tuple(list(xs)))


@composite
def gen_type(draw: DrawFn, depth: int = DEFAULT_DEPTH) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
    """Depth bounds recursion by forcing base at depth<=0.
    """
    types = ["base"]
    if depth >= 1:
        types.extend(["list", "dict", "tuple"])
    if depth >= 2:
        types.append("union")

    choice = draw(st.sampled_from(types))
    match choice:
        case "base":
            return draw(gen_base())
        case "list":
            return draw(gen_list(depth))
        case "dict":
            return draw(gen_dict(depth))
        case "union":
            return draw(gen_union(depth))
        case "tuple":
            return draw(gen_tuple(depth))
        case _:
            raise Exception(f"Programming error: '{choice}' not in {types}")


# -------------------- (Optional) arguments generator can use gen_type(depth) --------------------

_FIRST = st.sampled_from(string.ascii_letters + "_")
_REST = st.text(string.ascii_letters + string.digits + "_", min_size=0, max_size=20)
IDENT = st.builds(str.__add__, _FIRST, _REST).filter(lambda s: not keyword.iskeyword(s))


def _bernoulli(p: float) -> SearchStrategy[bool]:
    return st.integers(0, 999).map(lambda x: x < int(p * 1000))


@composite
def gen_arguments(
    draw: DrawFn,
    *,
    depth: int = DEFAULT_DEPTH,
    max_posonly: int = 2,
    max_args: int = 3,
    max_kwonly: int = 3,
    p_annot: float = 0.5,
    p_kwonly_default: float = 0.5,
) -> ast.arguments:
    tv = gen_type(depth)

    n_pos = draw(st.integers(0, max_posonly))
    n_args = draw(st.integers(0, max_args))
    n_kw = draw(st.integers(0, max_kwonly))
    use_vararg = draw(st.booleans())
    use_kwarg = draw(st.booleans())

    total = n_pos + n_args + n_kw + use_vararg + use_kwarg
    names = draw(st.lists(IDENT, min_size=total, max_size=total, unique=True))
    it = iter(names)

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

    posonlyargs = [_build_arg(next(it), anns[i]) for i in range(n_pos)]
    args = [_build_arg(next(it), anns[n_pos + j]) for j in range(n_args)]

    kwonlyargs: list[ast.arg] = []
    kw_defaults: list[ast.expr | None] = []
    for _ in range(n_kw):
        name = next(it)
        do_ann = draw(_bernoulli(p_annot))
        do_def = draw(_bernoulli(p_kwonly_default))
        if do_ann and do_def:
            t, vg = draw(tv)
            kwonlyargs.append(_build_arg(name, t))
            kw_defaults.append(draw(vg))
        elif do_ann:
            t, _vg = draw(tv)
            kwonlyargs.append(_build_arg(name, t))
            kw_defaults.append(None)
        elif do_def:
            _t, vg = draw(tv)
            kwonlyargs.append(_build_arg(name, None))
            kw_defaults.append(draw(vg))
        else:
            kwonlyargs.append(_build_arg(name, None))
            kw_defaults.append(None)

    vararg = None
    if use_vararg:
        name = next(it)
        ann = draw(tv)[0] if draw(_bernoulli(p_annot)) else None
        vararg = _build_arg(name, ann)

    kwarg = None
    if use_kwarg:
        name = next(it)
        ann = draw(tv)[0] if draw(_bernoulli(p_annot)) else None
        kwarg = _build_arg(name, ann)

    return ast.arguments(
        posonlyargs=posonlyargs,
        args=args,
        vararg=vararg,
        kwonlyargs=kwonlyargs,
        kw_defaults=kw_defaults,
        kwarg=kwarg,
        defaults=defaults,
    )

import ast
from dataclasses import dataclass
from typing import Sequence
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy, composite, DrawFn

# ============================================================
# Private AST builders (module-local, as requested)
# ============================================================

def _build_name(id_: str) -> ast.Name:
    return ast.Name(id=id_, ctx=ast.Load())

def _build_subscript(value: ast.expr, slice_expr: ast.expr) -> ast.Subscript:
    # Python 3.9+ expects an ast.expr (no ast.Index wrapper)
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
    it = iter(exprs)
    acc = next(it)
    for e in it:
        acc = ast.BinOp(left=acc, op=ast.BitOr(), right=e)
    return acc

def _build_tuple_type_slice(type_args: list[ast.expr]) -> ast.expr:
    """
    Build the slice part of `tuple[...]`.
    - For N > 0: tuple[T1, T2, ...]  -> slice = (T1, T2, ...)
    - For N = 0: tuple[()]           -> slice = ((),)  i.e., a 1-tuple containing the empty tuple
    """
    if len(type_args) == 0:
        # tuple[()]  => slice is a one-element tuple whose element is an empty tuple
        return _build_tuple([_build_tuple([])])
    else:
        return _build_tuple(type_args)


# ============================================================
# Base types and their AST Constant value strategies
# ============================================================

_BASE_VALUE_STRATS: dict[str, SearchStrategy[ast.expr]] = {
    "bool":  st.builds(ast.Constant, st.booleans()),
    "int":   st.builds(ast.Constant, st.integers(min_value=-1000, max_value=1000)),
    "str":   st.builds(ast.Constant, st.text(min_size=0, max_size=5)),
    "float": st.builds(ast.Constant, st.floats(allow_nan=False, allow_infinity=False, width=32)),
    "bytes": st.builds(ast.Constant, st.binary(min_size=0, max_size=5)),
}
_BASE_TYPE_NAMES = st.sampled_from(list(_BASE_VALUE_STRATS.keys()))

def _values_for(tname: str) -> SearchStrategy[ast.expr]:
    return _BASE_VALUE_STRATS[tname]


# ============================================================
# Config for size/depth controls (defaults favor corner cases)
# ============================================================

@dataclass(frozen=True)
class RecGenConfig:
    max_depth: int = 2                    # recursion depth (0 = base only)
    list_min_len: int = 0                 # allow empty lists by default
    list_max_len: int = 4
    tuple_min_arity: int = 0              # allow empty tuple types and values by default
    tuple_max_arity: int = 3
    dict_min_size: int = 0                # allow empty dicts by default
    dict_max_size: int = 3
    union_min_arms: int = 2               # unions are meaningful with >=2 arms
    union_max_arms: int = 4
    include_base: bool = True
    include_list: bool = True
    include_tuple: bool = True
    include_dict: bool = True
    include_union: bool = True

    # NOTE: For simplicity and correctness, dict keys are restricted to BASE types (hashable).
    #       If you want tuple-keys etc., we can extend with a “hashable subtype” generator.


# ============================================================
# Leaf/base: (type_expr, value_gen)
# ============================================================

def _base_type_and_gen() -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
    return _BASE_TYPE_NAMES.map(lambda t: (_build_name(t), _values_for(t)))


# ============================================================
# Recursive node factory (depth-bounded)
# ============================================================

def recursive_type_and_value_generator(
    config: RecGenConfig = RecGenConfig(),
) -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
    """
    Returns a depth-bounded recursive strategy yielding:
        (type_expr: ast.expr, value_gen: SearchStrategy[ast.expr])

    Supported shapes (PEP 585/604 forms):
      - Base:    int / str / bool / bytes / float
      - List:    list[T]
      - Tuple:   tuple[T1, T2, ...] and the empty case tuple[()]
      - Dict:    dict[K, V]  (K restricted to base types to ensure hashability)
      - Union:   T1 | T2 | ...

    Values are generated lazily via the returned SearchStrategy.
    """

    # Build a factory that returns a strategy at a given remaining depth.
    def _node(depth: int) -> SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]:
        if depth <= 0:
            # Base-only at depth 0
            return _base_type_and_gen()

        choices: list[SearchStrategy[tuple[ast.expr, SearchStrategy[ast.expr]]]] = []

        # Always include base if requested (improves shrinking and provides leaves at any depth)
        if config.include_base:
            choices.append(_base_type_and_gen())

        # ---------- list[T] ----------
        if config.include_list:
            @composite
            def _list_case(draw: DrawFn) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
                # Choose element type recursively
                elem_type_expr, elem_value_gen = draw(_node(depth - 1))
                type_expr = _build_subscript(_build_name("list"), elem_type_expr)

                k = draw(st.integers(min_value=config.list_min_len, max_value=config.list_max_len))
                value_gen = st.lists(elem_value_gen, min_size=k, max_size=k).map(_build_list)
                return (type_expr, value_gen)
            choices.append(_list_case())

        # ---------- tuple[T1, T2, ...] including empty ----------
        if config.include_tuple:
            @composite
            def _tuple_case(draw: DrawFn) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
                arity = draw(st.integers(min_value=config.tuple_min_arity, max_value=config.tuple_max_arity))

                if arity == 0:
                    type_expr = _build_subscript(_build_name("tuple"), _build_tuple_type_slice([]))
                    value_gen = st.just(_build_tuple([]))
                    return (type_expr, value_gen)

                # Draw each element type recursively
                members = [draw(_node(depth - 1)) for _ in range(arity)]
                elem_types = [t for (t, _vg) in members]
                elem_value_gens = [vg for (_t, vg) in members]

                type_expr = _build_subscript(_build_name("tuple"), _build_tuple_type_slice(elem_types))
                value_gen = st.tuples(*elem_value_gens).map(lambda elts: _build_tuple(list(elts)))
                return (type_expr, value_gen)
            choices.append(_tuple_case())

        # ---------- dict[K, V]  (K is BASE type for hashability) ----------
        if config.include_dict:
            @composite
            def _dict_case(draw: DrawFn) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
                # Key type MUST be base to ensure runtime hashability
                key_tname = draw(_BASE_TYPE_NAMES)
                key_type_expr = _build_name(key_tname)
                key_value_gen = _values_for(key_tname)

                # Value type is recursive
                val_type_expr, val_value_gen = draw(_node(depth - 1))
                type_expr = _build_subscript(
                    _build_name("dict"),
                    _build_tuple([key_type_expr, val_type_expr])
                )

                size = draw(st.integers(min_value=config.dict_min_size, max_value=config.dict_max_size))
                # TODO: Why is `size` needed? Why not use the range directly in keys_gen?
                keys_gen = st.lists(key_value_gen, min_size=size, max_size=size)
                # TODO: The compiler allows the same key to appear multiple times.
                # But is that meaningful? If not, add argument `unique=True`
                vals_gen = st.lists(val_value_gen, min_size=size, max_size=size)
                # TODO: Use size of keys_gen? 
                value_gen = st.tuples(keys_gen, vals_gen).map(lambda kv: _build_dict(kv[0], kv[1]))
                return (type_expr, value_gen)
            choices.append(_dict_case())

        # ---------- union: T1 | T2 | ... ----------
        if config.include_union:
            @composite
            def _union_case(draw: DrawFn) -> tuple[ast.expr, SearchStrategy[ast.expr]]:
                arms = draw(st.integers(min_value=config.union_min_arms, max_value=config.union_max_arms))
                # Draw arm types; allow duplicates (the parser allows it)
                # TODO is it meaningfull?
                members = [draw(_node(depth - 1)) for _ in range(arms)]
                type_exprs = [t for (t, _vg) in members]
                value_gens = [vg for (_t, vg) in members]

                type_expr = _build_bitor_chain(type_exprs)
                value_gen = st.one_of(*value_gens)
                return (type_expr, value_gen)
            choices.append(_union_case())

        # At this depth, choose among enabled shapes
        return st.one_of(*choices)

    # Kick off at configured max depth
    return _node(config.max_depth)
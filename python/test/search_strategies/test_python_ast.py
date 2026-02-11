import ast
from hypothesis import given, strategies as st

from test.search_strategies.python_type_and_value import recursive_type_and_value_generator, RecGenConfig

# 1) Ensure empty containers are possible (corner cases)
conf_empty = RecGenConfig(
    max_depth=1,
    include_base=True,
    include_list=True,
    include_tuple=True,
    include_dict=True,
    include_union=False,      # unions off for this test
    list_min_len=0, list_max_len=0,
    dict_min_size=0, dict_max_size=0,
    tuple_min_arity=0, tuple_max_arity=0,
)

@given(recursive_type_and_value_generator(conf_empty), st.data())
def test_empty_containers_are_possible(pair : tuple[ast.expr, st.SearchStrategy[ast.expr]], 
                                       data : st.DataObject) -> None:
    _type_expr, value_gen = pair
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    # empty list, dict, tuple or a scalar constant (allowed at depth 1)
    assert s in ("[]", "{}", "()") or isinstance(value_expr, ast.Constant)


# 2) Focus specifically on unions (no other composites)
conf_union_only = RecGenConfig(
    max_depth=2,
    include_base=True,        # allow base as recursive leaves
    include_list=False,
    include_tuple=False,
    include_dict=False,
    include_union=True,       # we are testing unions
    union_min_arms=2, union_max_arms=3,
)

@given(recursive_type_and_value_generator(conf_union_only), st.data())
def test_union_types_unparse_with_pipe(pair : tuple[ast.expr, st.SearchStrategy[ast.expr]], 
                                       data : st.DataObject) -> None:
    type_expr, value_gen = pair
    # In this config, composite constructs other than unions are disabled.
    # When depth>0 is taken, we should get a union (or base if depth shrinks),
    # but with union enabled and max_depth=2, unions should be exercised.
    s = ast.unparse(type_expr)
    if "|" in s:
        # If it's a union type, draw a matching value and compile an annotated assign
        value_expr = data.draw(value_gen)
        mod = ast.Module(
            body=[ast.AnnAssign(
                target=ast.Name(id="x", ctx=ast.Store()),
                annotation=type_expr,
                value=value_expr,
                simple=1,
            )],
            type_ignores=[],
        )
        ast.fix_missing_locations(mod)
        compile(mod, "<hypothesis>", "exec")

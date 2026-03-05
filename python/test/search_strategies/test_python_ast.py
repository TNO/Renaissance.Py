import ast

from hypothesis import given, strategies as st
from python_type_and_value import arguments_from_types, list_type_and_value, type_and_value, union_type_and_value


@given(arguments_from_types(depth=3, tv=union_type_and_value(3)))
def test_union_focused_compiles(a: ast.arguments):
    f = ast.FunctionDef(
        name="f", args=a, body=[ast.Pass()], decorator_list=[], returns=None
    )
    m = ast.Module(body=[f], type_ignores=[])
    ast.fix_missing_locations(m)
    compile(m, "<hypothesis>", "exec")


@given(list_type_and_value(depth=0), st.data())
def test_empty_list(
    pair: tuple[ast.expr, st.SearchStrategy[ast.expr]],
    data: st.DataObject,
) -> None:
    _type_expr, value_gen = pair
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    assert s == "[]"


@given(type_and_value(depth=1), st.data())
def test_empty_containers_are_possible(
    pair: tuple[ast.expr, st.SearchStrategy[ast.expr]],
    data: st.DataObject,
) -> None:
    _type_expr, value_gen = pair
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    # empty list, dict, tuple or a scalar constant (allowed at depth 1)
    assert s in ("[]", "{}", "()") or isinstance(value_expr, ast.Constant)

import ast
import re

from hypothesis import given, strategies as st
from python_type_and_value import gen_list, gen_union, gen_tuple, gen_dict

@given(gen_union())
def test_gen_union(
    pair: tuple[ast.expr, st.SearchStrategy[ast.expr]]
) -> None:   
    _type_expr, _value_gen = pair
    s = ast.unparse(_type_expr)
    assert re.match("^.*\\|.*$", s), f"type '{s}' unexpectedly doesn't match pattern"


@given(gen_list(), st.data())
def test_gen_list(
    pair: tuple[ast.expr, st.SearchStrategy[ast.expr]],
    data: st.DataObject
) -> None:   
    _type_expr, value_gen = pair
    s = ast.unparse(_type_expr)
    assert re.match("^list\\[.*\\]$", s), f"type '{s}' unexpectedly doesn't match pattern"
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    assert re.match("^\\[.*\\]$", s), f"value '{s}' unexpectedly doesn't match pattern"


    
@given(gen_tuple(), st.data())
def test_gen_tuple(
    pair: tuple[ast.expr, st.SearchStrategy[ast.expr]],
    data: st.DataObject
) -> None:   
    _type_expr, value_gen = pair
    s = ast.unparse(_type_expr)
    assert re.match("^tuple\\[.*\\]$", s), f"type '{s}' unexpectedly doesn't match pattern"
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    assert re.match("^\\(.*\\)$", s), f"value '{s}' unexpectedly doesn't match pattern"


@given(gen_dict(), st.data())
def test_gen_dict(
    pair: tuple[ast.expr, st.SearchStrategy[ast.expr]],
    data: st.DataObject
) -> None:   
    _type_expr, value_gen = pair
    s = ast.unparse(_type_expr)
    assert re.match("^dict\\[.*\\]$", s), f"type '{s}' unexpectedly doesn't match pattern"
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    assert re.match("^{.*}$", s), f"value '{s}' unexpectedly doesn't match pattern"
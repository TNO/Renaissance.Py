import ast
import re

from hypothesis import given, strategies as st
from python_type_and_value import gen_list, gen_union, gen_tuple, gen_dict


@given(gen_union())
def test_gen_union(pair: tuple[ast.expr, st.SearchStrategy[ast.expr]]) -> None:
    type_expr, _value_gen = pair
    assert isinstance(type_expr, ast.BinOp), f"Unexpected type '{type(type_expr)}', expected ast.BinOp"
    assert isinstance(type_expr.op, ast.BitOr), f"Unexpected operator '{type_expr.op}', expected ast.BitOr"
    s = ast.unparse(type_expr)
    assert re.match("^.*\\|.*$", s), f"type '{s}' unexpectedly doesn't match pattern"


@given(gen_list(), st.data())
def test_gen_list(pair: tuple[ast.expr, st.SearchStrategy[ast.expr]], data: st.DataObject) -> None:
    type_expr, value_gen = pair
    assert isinstance(type_expr, ast.Subscript), f"Unexpected type '{type(type_expr)}', expected ast.Subscript"
    assert isinstance(type_expr.value, ast.Name), f"Unexpected type '{type(type_expr)}', expected ast.Name"
    s = ast.unparse(type_expr)
    assert re.match("^list\\[.*\\]$", s), f"type '{s}' unexpectedly doesn't match pattern"
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    assert re.match("^\\[.*\\]$", s), f"value '{s}' unexpectedly doesn't match pattern"


@given(gen_tuple(), st.data())
def test_gen_tuple(pair: tuple[ast.expr, st.SearchStrategy[ast.expr]], data: st.DataObject) -> None:
    type_expr, value_gen = pair
    assert isinstance(type_expr, ast.Subscript), f"Unexpected type '{type(type_expr)}', expected ast.Subscript"
    assert isinstance(type_expr.value, ast.Name), f"Unexpected type '{type(type_expr)}', expected ast.Name"
    s = ast.unparse(type_expr)
    assert re.match("^tuple\\[.*\\]$", s), f"type '{s}' unexpectedly doesn't match pattern"
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    assert re.match("^\\(.*\\)$", s), f"value '{s}' unexpectedly doesn't match pattern"


@given(gen_dict(), st.data())
def test_gen_dict(pair: tuple[ast.expr, st.SearchStrategy[ast.expr]], data: st.DataObject) -> None:
    type_expr, value_gen = pair
    assert isinstance(type_expr, ast.Subscript), f"Unexpected type '{type(type_expr)}', expected ast.Subscript"
    assert isinstance(type_expr.value, ast.Name), f"Unexpected type '{type(type_expr)}', expected ast.Name"
    s = ast.unparse(type_expr)
    assert re.match("^dict\\[.*\\]$", s), f"type '{s}' unexpectedly doesn't match pattern"
    value_expr = data.draw(value_gen)
    s = ast.unparse(value_expr)
    assert re.match("^{.*}$", s), f"value '{s}' unexpectedly doesn't match pattern"

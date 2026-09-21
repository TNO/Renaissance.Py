"""Tests for the generated Python function-argument search strategies."""

# test_arguments_from_recursive.py
import ast

from hypothesis import given
from python_type_and_value import gen_arguments


def _collect_names(a: ast.arguments) -> list[str]:
    """AI: Collect all parameter names from an ast.arguments node in declaration order."""
    names: list[str] = []
    names.extend([x.arg for x in a.posonlyargs])
    names.extend([x.arg for x in a.args])
    names.extend([x.arg for x in a.kwonlyargs])
    if a.vararg is not None:
        names.append(a.vararg.arg)
    if a.kwarg is not None:
        names.append(a.kwarg.arg)
    return names


@given(gen_arguments())
def test_gen_arguments_names_unique(a: ast.arguments):
    """AI: Assert generated argument names are all unique."""
    names = _collect_names(a)
    assert len(names) == len(set(names))


@given(gen_arguments())
def test_gen_arguments_defaults_valid(a: ast.arguments):
    """AI: Assert the number of positional defaults never exceeds the number of positional arguments."""
    total_pos = len(a.args) + len(a.posonlyargs)
    assert len(a.defaults) <= total_pos


@given(gen_arguments())
def test_gen_arguments_compilable(a: ast.arguments):
    """AI: Assert a function built from generated arguments compiles successfully."""
    f = ast.FunctionDef(name="f", args=a, body=[ast.Pass()], decorator_list=[], returns=None)
    m = ast.Module(body=[f], type_ignores=[])
    ast.fix_missing_locations(m)
    compile(m, "<hypothesis>", "exec")


@given(gen_arguments())
def test_gen_arguments_unparsable_parsable(a: ast.arguments):
    """AI: Assert generated arguments unparse to source that can be re-parsed."""
    code = ast.unparse(a)
    ast.parse(f"""
def f({code}):
    pass
""")

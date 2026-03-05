# test_arguments_from_recursive.py
import ast
from hypothesis import given
from python_type_and_value import arguments_from_types


def _collect_names(a: ast.arguments) -> list[str]:
    names: list[str] = []
    names.extend([x.arg for x in a.posonlyargs])
    names.extend([x.arg for x in a.args])
    names.extend([x.arg for x in a.kwonlyargs])
    if a.vararg is not None:
        names.append(a.vararg.arg)
    if a.kwarg is not None:
        names.append(a.kwarg.arg)
    return names


@given(arguments_from_types())
def test_names_unique(a: ast.arguments):
    names = _collect_names(a)
    assert len(names) == len(set(names))


@given(arguments_from_types())
def test_defaults_layout_valid(a: ast.arguments):
    total_pos = len(a.args) + len(a.posonlyargs)
    assert len(a.defaults) <= total_pos
    # Assemble a compilable function to sanity check AST validity
    f = ast.FunctionDef(
        name="f",
        args=a,
        body=[ast.Pass()],
    )
    mod = ast.Module(body=[f], type_ignores=[])
    ast.fix_missing_locations(mod)
    compile(mod, "<hypothesis>", "exec")


@given(arguments_from_types())
def test_unparse_parse(a: ast.arguments):
    code = ast.unparse(a)
    print(code)
    ast.parse(
        f"""
def f({code}):
    pass
"""
    )

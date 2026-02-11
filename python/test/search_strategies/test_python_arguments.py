# test_arguments_from_recursive.py
import ast
from hypothesis import given

from python_arguments import arguments_from_recursive
from python_type_and_value import RecGenConfig


def _collect_names(a: ast.arguments) -> list[str]:
    names: list[str] = []
    names.extend([x.arg for x in getattr(a, "posonlyargs", [])])
    names.extend([x.arg for x in a.args])
    names.extend([x.arg for x in a.kwonlyargs])
    if a.vararg is not None:
        names.append(a.vararg.arg)
    if a.kwarg is not None:
        names.append(a.kwarg.arg)
    return names


@given(arguments_from_recursive(rec_config=RecGenConfig(max_depth=2)))
def test_names_unique(a: ast.arguments):
    names = _collect_names(a)
    assert len(names) == len(set(names))


@given(arguments_from_recursive(rec_config=RecGenConfig(max_depth=2)))
def test_defaults_layout_valid(a: ast.arguments):
    total_pos = len(a.args) + len(getattr(a, "posonlyargs", []))
    assert len(a.defaults) <= total_pos
    # Assemble a compilable function to sanity check AST validity
    f = ast.FunctionDef(
        name="f",
        args=a,
        body=[ast.Pass()],
        decorator_list=[],
        returns=None,
        type_comment=None,
    )
    mod = ast.Module(body=[f], type_ignores=[])
    ast.fix_missing_locations(mod)
    compile(mod, "<hypothesis>", "exec")


# Optional: exercise corner cases by restricting sizes and keeping depth small
@given(
    arguments_from_recursive(
        max_posonly=2,
        max_args=2,
        max_kwonly=2,
        rec_config=RecGenConfig(
            max_depth=1,
            list_min_len=0,
            list_max_len=0,  # empty lists only
            dict_min_size=0,
            dict_max_size=0,  # empty dicts only
            tuple_min_arity=0,
            tuple_max_arity=0,  # empty tuple only
            include_base=True,
            include_list=True,
            include_tuple=True,
            include_dict=True,
            include_union=True,
        ),
    )
)
def test_corner_empty_containers_compile(a: ast.arguments):
    f = ast.FunctionDef(
        name="g", args=a, body=[ast.Pass()], decorator_list=[], returns=None
    )
    mod = ast.Module(body=[f], type_ignores=[])
    ast.fix_missing_locations(mod)
    compile(mod, "<hypothesis>", "exec")


@given(
    arguments_from_recursive(
        max_posonly=2,
        max_args=2,
        max_kwonly=2,
        rec_config=RecGenConfig(
            max_depth=4,
            list_min_len=0,
            list_max_len=4,
            dict_min_size=0,
            dict_max_size=4,
            tuple_min_arity=0,
            tuple_max_arity=4,
            include_base=True,
            include_list=True,
            include_tuple=True,
            include_dict=True,
            include_union=True,
        ),
    )
)
def test_unparse_parse(a: ast.arguments):
    code = ast.unparse(a)
    print(code)
    ast.parse(
        f"""
def f({code}):
    pass
"""
    )

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Read and rewrite the declaration of a TypeVar/ParamSpec/TypeVarTuple: `NAME = TypeVar(...)`."""

import builtins
from collections.abc import Iterable
from typing import cast

import libcst as cst

from renaissance.utils.cst_utils import module_statements, names_read_by

_CONSTRUCTORS = frozenset({"TypeVar", "ParamSpec", "TypeVarTuple"})


def _is_type_param_call(value: cst.BaseExpression) -> bool:
    """Return True if `value` is a call to TypeVar/ParamSpec/TypeVarTuple."""
    return isinstance(value, cst.Call) and isinstance(value.func, cst.Name) and value.func.value in _CONSTRUCTORS


def find_type_param_declarations(module: cst.Module) -> dict[str, cst.Assign]:
    """Find every module-level "NAME = TypeVar/ParamSpec/TypeVarTuple(...)" declaration."""
    declarations: dict[str, cst.Assign] = {}
    for statement in module_statements(module):
        if isinstance(statement, cst.Assign) and _is_type_param_call(statement.value):
            for target in statement.targets:
                if isinstance(target.target, cst.Name):
                    declarations[target.target.value] = statement
    return declarations


def declaration_text(module: cst.Module, decl_stmt: cst.Assign) -> str:
    """Return decl_stmt as written in module, without its `;`.

    The comment trailing its line follows it when it is the only statement there, since on a shared
    line the comment may belong to another statement.
    """
    text = module.code_for_node(decl_stmt.with_changes(semicolon=cst.MaybeSentinel.DEFAULT))
    trailing = trailing_of_sole_statement(module, decl_stmt)
    if trailing is not None and trailing.comment is not None:
        text += module.code_for_node(trailing.whitespace) + module.code_for_node(trailing.comment)
    return text


def trailing_of_sole_statement(module: cst.Module, statement: cst.BaseSmallStatement) -> cst.TrailingWhitespace | None:
    """Return the whitespace and comment trailing the line of statement in module, or None if the line holds others."""
    for line in module.body:
        if isinstance(line, cst.SimpleStatementLine) and len(line.body) == 1 and line.body[0] is statement:
            return line.trailing_whitespace
    return None


def _call(decl_stmt: cst.Assign) -> cst.Call:
    """Return the TypeVar/ParamSpec/TypeVarTuple call a declaration assigns."""
    return cast("cst.Call", decl_stmt.value)


def _positional_arguments(call: cst.Call) -> list[cst.Arg]:
    """Return the call's positional arguments, `*args` included."""
    return [argument for argument in call.args if argument.keyword is None and argument.star != "**"]


def _keyword_value(call: cst.Call, keyword: str) -> cst.BaseExpression | None:
    """Return the value the call passes as `keyword=`, or None if it passes none."""
    return next((argument.value for argument in call.args if argument.keyword is not None and argument.keyword.value == keyword), None)


def type_param_constructor_name(decl_stmt: cst.Assign) -> str:
    """Return the name of the call a declaration uses, e.g. "TypeVar" for `T = TypeVar("T")`."""
    return cast("cst.Name", _call(decl_stmt).func).value


def string_value(expression: cst.BaseExpression) -> str | None:
    """Return the value of a plain or concatenated string literal, or None for any other expression."""
    if isinstance(expression, cst.SimpleString | cst.ConcatenatedString):
        value = expression.evaluated_value
        return value if isinstance(value, str) else None
    return None


def declaration_argument_names(decl_stmt: cst.Assign) -> set[str]:
    """Return the non-builtin names a declaration's arguments use, e.g. {"Shape"} for `TypeVar("T", bound=Shape)`.

    The first positional argument (the type parameter's own name) is skipped; a string argument is read as a
    forward reference (`bound="Shape"`). A string that isn't a valid expression contributes no names.
    """
    call = _call(decl_stmt)
    keyword_arguments = [argument for argument in call.args if argument.keyword is not None or argument.star == "**"]
    names: set[str] = set()
    for argument in [*_positional_arguments(call)[1:], *keyword_arguments]:
        expression = argument.value
        text = string_value(expression)
        if text is not None:
            try:
                expression = cst.parse_expression(text)
            except cst.ParserSyntaxError:
                continue
        names |= names_read_by(expression)
    return names - set(dir(builtins))


# Variance needs no syntax of its own: a PEP 695 type parameter always infers it, and a function's has none.
_CONVERTIBLE_KEYWORDS: dict[str, frozenset[str]] = {
    "TypeVar": frozenset({"bound", "default", "infer_variance", "covariant", "contravariant"}),
    "ParamSpec": frozenset({"default", "infer_variance", "covariant", "contravariant"}),
    "TypeVarTuple": frozenset({"default", "infer_variance"}),
}


def declared_default(decl_stmt: cst.Assign) -> cst.BaseExpression | None:
    """Return the value a legacy declaration passes as `default=` (PEP 696), or None if it passes none."""
    return _keyword_value(_call(decl_stmt), "default")


def has_unconvertible_argument(decl_stmt: cst.Assign) -> bool:
    """Return True if a legacy declaration passes a keyword type_param_text can't carry over.

    That is any keyword outside the constructor's known set, e.g. `bound=` on a ParamSpec or TypeVarTuple,
    a keyword added by a later Python version, or a `**mapping`.
    """
    convertible = _CONVERTIBLE_KEYWORDS[type_param_constructor_name(decl_stmt)]
    return any(
        argument.star == "**" or (argument.keyword is not None and argument.keyword.value not in convertible)
        for argument in _call(decl_stmt).args
    )


def type_param_text(decl_stmt: cst.Assign, module: cst.Module) -> str:
    """Return the PEP 695 type parameter equivalent to a legacy declaration from `module`, in its original formatting.

    E.g. `T = TypeVar("T", bound=int, default=int)` gives `T: int = int`. Bounds, constraints and
    `default=` are carried over; `infer_variance=`, `covariant=` and `contravariant=` are dropped. Callers must
    first reject declarations for which has_unconvertible_argument() is True.
    """
    call = _call(decl_stmt)
    constructor = type_param_constructor_name(decl_stmt)
    positional = _positional_arguments(call)
    name = cast("str", cast("cst.SimpleString", positional[0].value).evaluated_value)

    if constructor == "ParamSpec":
        text = f"**{name}"
    elif constructor == "TypeVarTuple":
        text = f"*{name}"
    else:
        text = name
        bound = _keyword_value(call, "bound")
        constraints = [f"{argument.star}{module.code_for_node(argument.value)}" for argument in positional[1:]]
        if bound is not None:
            text += f": {module.code_for_node(bound)}"
        elif constraints:
            # A single constraint keeps a trailing comma, or the parentheses would make it a bound.
            text += f": ({', '.join(constraints)}{',' if len(constraints) == 1 else ''})"

    default = declared_default(decl_stmt)
    if default is not None:
        text += f" = {module.code_for_node(default)}"
    return text


def type_params_bracket(params: Iterable[tuple[str, bool]]) -> str:
    """Return the `[...]` bracket for type parameters given as (text, has_default), with the defaulted ones last.

    The relative order within each group is kept. A non-default type parameter following a defaulted
    one is a SyntaxError.
    """
    ordered = sorted(params, key=lambda param: param[1])
    return f"[{', '.join(text for text, _ in ordered)}]"

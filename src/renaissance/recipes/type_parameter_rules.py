# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""TypeVar/ParamSpec/TypeVarTuple domain model and safety analysis."""

import builtins
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

import libcst as cst

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.utils.cst_utils import module_statements, names_read_by
from renaissance.utils.import_resolution import imports_name_conditionally

PEP_696_MINIMUM = (3, 13)
DOCS_BASE_URL = "https://tno.github.io/Renaissance.Py/user/features/type-parameter-modernization/"


class UnsafeReason(StrEnum):
    """Every distinct, permanent reason a TypeVar/ParamSpec/TypeVarTuple candidate is left unconverted.

    Each member has a matching documented rule under DOCS_BASE_URL - see UNSAFE_RULES.
    """

    PEP696_VERSION_GATE = "pep696_version_gate"
    NO_PEP695_EQUIVALENT = "no_pep695_equivalent"
    DECLARED_TYPEVAR_EXPORTED = "declared_typevar_exported"
    USED_IN_GENERIC_CLASS = "used_in_generic_class"
    SHARES_FUNCTION_WITH_UNCONVERTIBLE = "shares_function_with_unconvertible"
    NAME_NOT_AT_MODULE_LEVEL = "name_not_at_module_level"
    IMPORTED_ELSEWHERE_IN_PROJECT = "imported_elsewhere_in_project"
    ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY = "origin_imports_constructor_conditionally"


@dataclass(frozen=True)
class UnsafeRule:
    """A short human-readable explanation plus the docs anchor slug for one UnsafeReason."""

    message: str
    doc_anchor: str


UNSAFE_RULES: dict[UnsafeReason, UnsafeRule] = {
    UnsafeReason.PEP696_VERSION_GATE: UnsafeRule(
        "declares a default= (PEP 696), which needs the target's minimum Python to be 3.13+",
        "feature-type-parameter-modernization-pep696-version-gate",
    ),
    UnsafeReason.NO_PEP695_EQUIVALENT: UnsafeRule(
        "declaration passes an argument with no PEP 695 equivalent, e.g. bound= on a ParamSpec or a **mapping",
        "feature-type-parameter-modernization-no-pep695-equivalent",
    ),
    UnsafeReason.DECLARED_TYPEVAR_EXPORTED: UnsafeRule(
        "exported via __all__",
        "feature-type-parameter-modernization-declared-type-parameter-exported",
    ),
    UnsafeReason.USED_IN_GENERIC_CLASS: UnsafeRule(
        "only used inside a class that is generic over it",
        "feature-type-parameter-modernization-used-in-generic-class",
    ),
    UnsafeReason.SHARES_FUNCTION_WITH_UNCONVERTIBLE: UnsafeRule(
        "every function using it also uses a type variable that can't be converted",
        "feature-type-parameter-modernization-shares-function-with-unconvertible",
    ),
    UnsafeReason.NAME_NOT_AT_MODULE_LEVEL: UnsafeRule(
        "declaration uses a name that isn't available at module level as the same object",
        "feature-type-parameter-modernization-name-not-at-module-level",
    ),
    UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT: UnsafeRule(
        "imported directly by another file in the target project",
        "feature-type-parameter-modernization-imported-elsewhere-in-project",
    ),
    UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY: UnsafeRule(
        "origin module imports TypeVar/ParamSpec/TypeVarTuple inside an if/try block, e.g. under TYPE_CHECKING or per Python version",
        "feature-type-parameter-modernization-origin-imports-constructor-conditionally",
    ),
}


_CONSTRUCTORS = frozenset({"TypeVar", "ParamSpec", "TypeVarTuple"})


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


def _string_value(expression: cst.BaseExpression) -> str | None:
    """Return the value of a plain or concatenated string literal, or None for any other expression."""
    if isinstance(expression, cst.SimpleString | cst.ConcatenatedString):
        value = expression.evaluated_value
        return value if isinstance(value, str) else None
    return None


def _find_dunder_all(module: cst.Module) -> set[str] | None:
    """Return the names in this module's plain `__all__ = [...]` assignment, or None if it has none.

    Only a list, tuple or set literal is read; annotated, `+=`, `.extend()` and `.append()` forms are ignored.
    """
    for statement in module_statements(module):
        if (
            isinstance(statement, cst.Assign)
            and any(isinstance(target.target, cst.Name) and target.target.value == "__all__" for target in statement.targets)
            and isinstance(statement.value, cst.List | cst.Tuple | cst.Set)
        ):
            values = (_string_value(element.value) for element in statement.value.elements if isinstance(element, cst.Element))
            return {value for value in values if value is not None}
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
        text = _string_value(expression)
        if text is not None:
            try:
                expression = cst.parse_expression(text)
            except cst.ParserSyntaxError:
                continue
        names |= names_read_by(expression)
    return names - set(dir(builtins))


@dataclass(frozen=True)
class RefusalRule[**P]:
    """One reason to refuse a type parameter, and the check that decides whether it applies.

    Attributes:
        reason: What the report says when the check refuses.
        refuses: Return True if the reason applies to the arguments the rule's stage passes.

    """

    reason: UnsafeReason
    refuses: Callable[P, bool]


def _first_refusal[**P](rules: Iterable[RefusalRule[P]], *args: P.args, **kwargs: P.kwargs) -> UnsafeReason | None:
    """Return the reason of the first rule that refuses, or None if none does."""
    return next((rule.reason for rule in rules if rule.refuses(*args, **kwargs)), None)


def _has_no_pep695_equivalent(declaration: cst.Assign, _min_python: tuple[int, int]) -> bool:
    """Return True if the declaration passes an argument that PEP 695 syntax can't carry over."""
    return has_unconvertible_argument(declaration)


def _needs_newer_python(declaration: cst.Assign, min_python: tuple[int, int]) -> bool:
    """Return True if the declaration has a `default=` (PEP 696) and min_python is below the 3.13 that introduced it."""
    return declared_default(declaration) is not None and min_python < PEP_696_MINIMUM


def _is_exported(module: cst.Module, name: str, _project_wide_imported_names: frozenset[str]) -> bool:
    """Return True if the module lists `name` in a plain `__all__ = [...]`."""
    dunder_all = _find_dunder_all(module)
    return dunder_all is not None and name in dunder_all


def _is_imported_elsewhere(_module: cst.Module, name: str, project_wide_imported_names: frozenset[str]) -> bool:
    """Return True if another file in the target project imports `name` directly, regardless of `__all__`."""
    return name in project_wide_imported_names


def _origin_imports_constructor_conditionally(origin: cst.Module, name: str) -> bool:
    """Return True if the origin imports the constructor of `name` inside a module-level `if`/`try` block.

    Which implementation the constructor binds then depends on the runtime or the type checker, e.g.
    `typing_extensions` below 3.13 or under `TYPE_CHECKING`.
    """
    declaration = find_type_param_declarations(origin).get(name)
    return declaration is not None and imports_name_conditionally(origin, type_param_constructor_name(declaration))


# Each stage reports the first rule that refuses, so the order is the order of precedence. Commenting out
# a rule switches it off; the rules a pipeline step enforces by its own structure are not listed here
# (USED_IN_GENERIC_CLASS, SHARES_FUNCTION_WITH_UNCONVERTIBLE, NAME_NOT_AT_MODULE_LEVEL).
CONVERSION_RULES: tuple[RefusalRule[[cst.Assign, tuple[int, int]]], ...] = (
    RefusalRule(UnsafeReason.NO_PEP695_EQUIVALENT, _has_no_pep695_equivalent),
    RefusalRule(UnsafeReason.PEP696_VERSION_GATE, _needs_newer_python),
)
REMOVAL_RULES: tuple[RefusalRule[[cst.Module, str, frozenset[str]]], ...] = (
    RefusalRule(UnsafeReason.DECLARED_TYPEVAR_EXPORTED, _is_exported),
    RefusalRule(UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT, _is_imported_elsewhere),
)
LOCALIZATION_RULES: tuple[RefusalRule[[cst.Module, str]], ...] = (
    RefusalRule(UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY, _origin_imports_constructor_conditionally),
)


def conversion_refusal(declaration: cst.Assign, min_python: tuple[int, int]) -> UnsafeReason | None:
    """Return None if `declaration` can become a PEP 695 type parameter on a target with `min_python`, else why not."""
    return _first_refusal(CONVERSION_RULES, declaration, min_python)


def is_safe_to_localize(origin: cst.Module, name: str) -> UnsafeReason | None:
    """Return None if `name` is safe to duplicate as a local declaration, else the reason it isn't."""
    return _first_refusal(LOCALIZATION_RULES, origin, name)


def is_safe_to_remove(
    module: cst.Module,
    name: str,
    project_wide_imported_names: frozenset[str] = frozenset(),
) -> UnsafeReason | None:
    """Return None if this file's own binding of `name` may be removed or replaced, else the reason it may not.

    `project_wide_imported_names` holds the names other files of the target project import from this one.
    """
    return _first_refusal(REMOVAL_RULES, module, name, project_wide_imported_names)


def uses_of(root: PythonCstNode, name: str, decl_stmt: cst.Assign) -> list[PythonCstNode]:
    """Return the nodes that use the module-level `name` that decl_stmt declares, resolved with libcst's scope analysis.

    A use inside a string annotation or `cast("T", x)` counts; a `T` that a PEP 695 type parameter of an
    enclosing function or class (`def f[T]`, `class C[T]`) declares does not.
    """
    target = next(target.target for target in decl_stmt.targets if isinstance(target.target, cst.Name) and target.target.value == name)
    return [reference.node for reference in root.translation_unit.wrappers[target].referenced_by]


def outermost_function(node: PythonCstNode) -> PythonCstNode | None:
    """Return the outermost function or method enclosing node, or None if node is outside every function."""
    outermost = None
    current = node.parent
    while current is not None:
        if isinstance(current.node, cst.FunctionDef):
            outermost = current
        current = current.parent
    return outermost


def generic_classes(uses: Iterable[PythonCstNode]) -> list[PythonCstNode]:
    """Return the classes that have one of `uses` in a base (`Generic[T]`, `Protocol[T]`, `Base[int, T]`).

    Such a class is generic over the used name.
    """
    classes: list[PythonCstNode] = []
    for use in uses:
        child, current = use, use.parent
        while current is not None:
            if isinstance(current.node, cst.ClassDef) and any(child.node is base for base in current.node.bases):
                if current not in classes:
                    classes.append(current)
                break
            child, current = current, current.parent
    return classes


def declares_type_param(function: cst.FunctionDef, name: str) -> bool:
    """Return True if the function declares `name` as its own PEP 695 type parameter (`def f[T](...)`)."""
    parameters = function.type_parameters
    return parameters is not None and any(parameter.param.name.value == name for parameter in parameters.params)


def signature_function(use: PythonCstNode) -> PythonCstNode | None:
    """Return the function whose parameter or return annotation contains use, or None if no signature does.

    A use in a function's body, a parameter default or a decorator is in no signature.
    """
    in_annotation = False
    child, current = use, use.parent
    while current is not None:
        if isinstance(current.node, cst.Annotation):
            in_annotation = True
        elif isinstance(current.node, cst.FunctionDef):
            return current if in_annotation and child.node is not current.node.body else None
        child, current = current, current.parent
    return None


def owning_function(node: PythonCstNode, signature_users: set[int]) -> PythonCstNode | None:
    """Return the outermost function enclosing node whose id is in signature_users, or None if there is none."""
    owner = None
    current = node.parent
    while current is not None:
        if isinstance(current.node, cst.FunctionDef) and id(current) in signature_users:
            owner = current
        current = current.parent
    return owner


def generic_classes(uses: Iterable[PythonCstNode]) -> list[PythonCstNode]:
    """Return the classes that have one of `uses` in a base (`Generic[T]`, `Protocol[T]`, `Base[int, T]`).

    Such a class is generic over the used name.
    """
    classes: list[PythonCstNode] = []
    for use in uses:
        child, current = use, use.parent
        while current is not None:
            if isinstance(current.node, cst.ClassDef) and any(child.node is base for base in current.node.bases):
                if current not in classes:
                    classes.append(current)
                break
            child, current = current, current.parent
    return classes


def declares_type_param(function: cst.FunctionDef, name: str) -> bool:
    """Return True if the function declares `name` as its own PEP 695 type parameter (`def f[T](...)`)."""
    parameters = function.type_parameters
    return parameters is not None and any(parameter.param.name.value == name for parameter in parameters.params)


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

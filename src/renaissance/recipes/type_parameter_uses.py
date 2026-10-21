# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Find where a module-level TypeVar/ParamSpec/TypeVarTuple name is used, with libcst's scope analysis."""

from collections.abc import Iterable

import libcst as cst

from renaissance.integrations.python.ast.cst_node import PythonCstNode


def uses_of(root: PythonCstNode, name: str, decl_stmt: cst.Assign) -> list[PythonCstNode]:
    """Return the nodes that use the module-level `name` that decl_stmt declares, resolved with libcst's scope analysis.

    A use inside a string annotation or `cast("T", x)` counts; a `T` that a PEP 695 type parameter of an
    enclosing function or class (`def f[T]`, `class C[T]`) declares does not.
    """
    target = next(target.target for target in decl_stmt.targets if isinstance(target.target, cst.Name) and target.target.value == name)
    return [reference.node for reference in root.translation_unit.wrappers[target].referenced_by]


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

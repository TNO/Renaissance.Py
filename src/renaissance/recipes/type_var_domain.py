"""TypeVar/ParamSpec/TypeVarTuple domain model and safety analysis.

Shared between TypeVarCheck and TypeVarTupleCheck, kept separate from either recipe's own
pipeline logic.
"""

import ast
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

DOCS_BASE_URL = "https://tno.github.io/Renaissance.Py/user/features/typevar-modernization/"


class UnsafeReason(StrEnum):
    """Every distinct, permanent reason a TypeVar/ParamSpec/TypeVarTuple candidate is left unconverted.

    Each member has a matching documented rule under DOCS_BASE_URL - see UNSAFE_RULES and doc_link().
    """

    PEP695_VERSION_GATE = "pep695_version_gate"
    PEP646_VERSION_GATE = "pep646_version_gate"
    DECLARED_TYPEVAR_EXPORTED = "declared_typevar_exported"
    USED_OUTSIDE_FUNCTION = "used_outside_function"
    ORIGIN_MODULE_EXPORTS_NAME = "origin_module_exports_name"
    USED_IN_EXPORTED_GENERIC_BASE = "used_in_exported_generic_base"


@dataclass(frozen=True)
class UnsafeRule:
    """A short human-readable explanation plus the docs anchor slug for one UnsafeReason."""

    message: str
    doc_anchor: str


UNSAFE_RULES: dict[UnsafeReason, UnsafeRule] = {
    UnsafeReason.PEP695_VERSION_GATE: UnsafeRule(
        "target codebase doesn't declare Python 3.12+", "feature-typevar-modernization-pep695-version-gate",
    ),
    UnsafeReason.PEP646_VERSION_GATE: UnsafeRule(
        "target codebase doesn't declare Python 3.11+", "feature-typevar-modernization-pep646-version-gate",
    ),
    UnsafeReason.DECLARED_TYPEVAR_EXPORTED: UnsafeRule(
        "exported via __all__", "feature-typevar-modernization-declared-typevar-exported",
    ),
    UnsafeReason.USED_OUTSIDE_FUNCTION: UnsafeRule(
        "used outside a function body, e.g. a Generic[...] base", "feature-typevar-modernization-used-outside-function",
    ),
    UnsafeReason.ORIGIN_MODULE_EXPORTS_NAME: UnsafeRule(
        "origin module exports it via __all__", "feature-typevar-modernization-origin-module-exports-name",
    ),
    UnsafeReason.USED_IN_EXPORTED_GENERIC_BASE: UnsafeRule(
        "used in a Generic[...] base at its origin module", "feature-typevar-modernization-used-in-exported-generic-base",
    ),
}


def doc_link(reason: UnsafeReason) -> str:
    """Return the full URL to the documented rule explaining why `reason` makes a candidate unsafe."""
    return f"{DOCS_BASE_URL}#{UNSAFE_RULES[reason].doc_anchor}"


def _is_type_param_call(value: ast.expr) -> bool:
    """Return True if `value` is a call to TypeVar/ParamSpec/TypeVarTuple."""
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in ("TypeVar", "ParamSpec", "TypeVarTuple")
    )


def find_type_param_declarations(tree: ast.Module) -> dict[str, ast.Assign]:
    """Find every module-level "NAME = TypeVar/ParamSpec/TypeVarTuple(...)" declaration."""
    declarations: dict[str, ast.Assign] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and _is_type_param_call(stmt.value):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    declarations[target.id] = stmt
    return declarations


def type_param_name(param: ast.type_param) -> str:
    """Return a PEP 695 type parameter's name.

    `ast.type_param`'s own stub doesn't declare `.name` - only its three concrete subclasses
    (`ast.TypeVar`/`ast.ParamSpec`/`ast.TypeVarTuple`) do, and every real type_param is one of
    them, so this narrows to get at it.
    """
    assert isinstance(param, ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple)
    return param.name


def type_param_constructor_name(decl_stmt: ast.Assign) -> str:
    """Return the name of the call a declaration uses, e.g. "TypeVar" for `T = TypeVar("T")`."""
    call = cast(ast.Call, decl_stmt.value)
    return cast(ast.Name, call.func).id


def _find_dunder_all(tree: ast.Module) -> set[str] | None:
    """Return the names listed in this module's `__all__`, or None if it doesn't declare one."""
    for stmt in tree.body:
        if (
            isinstance(stmt, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets)
            and isinstance(stmt.value, ast.List | ast.Tuple | ast.Set)
        ):
            return {
                elt.value
                for elt in stmt.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            }
    return None


def _used_in_exported_generic_base(tree: ast.Module, name: str) -> bool:
    """Return True if `name` appears inside a `Generic[...]` base of any class in this module."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if not isinstance(base, ast.Subscript):
                continue
            if not (isinstance(base.value, ast.Name) and base.value.id == "Generic"):
                continue
            for inner in ast.walk(base.slice):
                if isinstance(inner, ast.Name) and inner.id == name:
                    return True
    return False


def is_safe_to_localize(origin_tree: ast.Module, name: str) -> UnsafeReason | None:
    """Return None if `name` is safe to duplicate as a local declaration, else the reason it isn't.

    The origin module must not advertise it as public API, whether via `__all__`
    (ORIGIN_MODULE_EXPORTS_NAME) or as a class-level `Generic[...]` parameter
    (USED_IN_EXPORTED_GENERIC_BASE, where identity crossing files can matter for subclassing).
    """
    dunder_all = _find_dunder_all(origin_tree)
    if dunder_all is not None and name in dunder_all:
        return UnsafeReason.ORIGIN_MODULE_EXPORTS_NAME
    if _used_in_exported_generic_base(origin_tree, name):
        return UnsafeReason.USED_IN_EXPORTED_GENERIC_BASE
    return None


def find_import_source(tree: ast.Module, name: str) -> str | None:
    """Which module a bare name (e.g. "TypeVar") was imported from in this file, e.g. "typing"."""
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module is not None:
            for alias in stmt.names:
                if (alias.asname or alias.name) == name:
                    return stmt.module
    return None


def resolve_sibling_module(importing_file: str, module_name: str) -> Path | None:
    """Resolve a simple "from module_name import ..." to a sibling .py file in the same directory.

    Dotted/package imports are out of scope for this recipe and always resolve to None.
    """
    if "." in module_name:
        return None
    candidate = Path(importing_file).parent / f"{module_name}.py"
    return candidate if candidate.is_file() else None


def functions_using_nodes(
    tree: ast.Module, names: set[str]
) -> dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Map each of `names` to the outermost function/method node whose signature or body references it.

    A name referenced inside a nested function (a closure) is attributed to the *outermost*
    function in its nesting chain, never the nested one - a PEP 695 type parameter declared on an
    enclosing function is already visible inside a nested closure the same way any other name in
    an enclosing scope is, so the nested function must never be treated as an independent user
    needing its own (shadowing) declaration. Getting this wrong doubled up as two bugs at once:
    semantically pointless shadowing declarations, and - combined with the still-open rewrite
    dominance/suppression gap - genuinely corrupted output, confirmed live against
    `starlette/starlette/authentication.py`'s `requires()` and its nested `*_wrapper` closures.
    See python-ast-known-limitations.md item 5.
    """
    usage: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {name: [] for name in names}

    def visit(node: ast.AST, enclosing: ast.FunctionDef | ast.AsyncFunctionDef | None) -> None:
        current = enclosing
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and enclosing is None:
            current = node
        if isinstance(node, ast.Name) and current is not None and node.id in usage and current not in usage[node.id]:
            usage[node.id].append(current)
        for child in ast.iter_child_nodes(node):
            visit(child, current)

    visit(tree, None)
    return usage


def _used_outside_functions(tree: ast.Module, name: str, decl_stmt: ast.Assign) -> bool:
    """Return True if `name` is referenced anywhere outside a function/method body.

    Other than its own declaration - e.g. a class's `Generic[...]` base or a module-level type
    alias.
    """

    def visit(node: ast.AST, in_function: bool) -> bool:
        if node is decl_stmt:
            return False
        if isinstance(node, ast.Name) and node.id == name and not in_function:
            return True
        current = in_function or isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        return any(visit(child, current) for child in ast.iter_child_nodes(node))

    return visit(tree, False)


def is_safe_to_convert(tree: ast.Module, name: str, decl_stmt: ast.Assign) -> UnsafeReason | None:
    """Return None if `name` is safe to convert to PEP 695 syntax and its declaration removed.

    Otherwise returns the reason it isn't: DECLARED_TYPEVAR_EXPORTED if exported via `__all__`,
    USED_OUTSIDE_FUNCTION if referenced anywhere outside the functions using it.
    """
    dunder_all = _find_dunder_all(tree)
    if dunder_all is not None and name in dunder_all:
        return UnsafeReason.DECLARED_TYPEVAR_EXPORTED
    if _used_outside_functions(tree, name, decl_stmt):
        return UnsafeReason.USED_OUTSIDE_FUNCTION
    return None


def all_refs_shadowed_by_pep695(tree: ast.Module, name: str, decl_stmt: ast.Assign) -> bool:
    """Return True if every remaining reference to `name` is shadowed by a PEP 695 type parameter.

    E.g. `def b[T](x: T) -> T:`, where `T` resolves to the function's own parameter rather than
    the module-level declaration, making it dead. Also true (vacuously) if `name` isn't
    referenced anywhere at all.
    """
    found_live_use = False

    def visit(node: ast.AST, shadowed: bool) -> None:
        nonlocal found_live_use
        if node is decl_stmt or found_live_use:
            return
        if isinstance(node, ast.Name) and node.id == name:
            if not shadowed:
                found_live_use = True
            return
        current = shadowed
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            current = any(type_param_name(param) == name for param in node.type_params)
        for child in ast.iter_child_nodes(node):
            visit(child, current)

    visit(tree, False)
    return not found_live_use


def build_type_param(decl_stmt: ast.Assign) -> ast.type_param:
    """Translate a legacy declaration into the equivalent PEP 695 type_param node.

    E.g. `T = TypeVar("T", bound=int)` becomes an `ast.TypeVar`/`ast.ParamSpec`/`ast.TypeVarTuple`.
    """
    call = cast(ast.Call, decl_stmt.value)
    ctor = cast(ast.Name, call.func).id
    name = cast(str, cast(ast.Constant, call.args[0]).value)

    if ctor == "ParamSpec":
        return ast.ParamSpec(name=name)
    if ctor == "TypeVarTuple":
        return ast.TypeVarTuple(name=name)

    bound = next((kw.value for kw in call.keywords if kw.arg == "bound"), None)
    constraints = call.args[1:]
    if bound is None and constraints:
        bound = ast.Tuple(elts=list(constraints), ctx=ast.Load())
    return ast.TypeVar(name=name, bound=bound)

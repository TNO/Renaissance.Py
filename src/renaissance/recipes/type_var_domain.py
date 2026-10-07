"""TypeVar/ParamSpec/TypeVarTuple domain model and safety analysis."""

import ast
import builtins
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

DOCS_BASE_URL = "https://tno.github.io/Renaissance.Py/user/features/typevar-modernization/"


class UnsafeReason(StrEnum):
    """Every distinct, permanent reason a TypeVar/ParamSpec/TypeVarTuple candidate is left unconverted.

    Each member has a matching documented rule under DOCS_BASE_URL - see UNSAFE_RULES and doc_link().
    """

    PEP695_VERSION_GATE = "pep695_version_gate"
    DECLARED_TYPEVAR_EXPORTED = "declared_typevar_exported"
    USED_IN_GENERIC_CLASS = "used_in_generic_class"
    DECLARATION_NAME_CONFLICT = "declaration_name_conflict"
    IMPORTED_ELSEWHERE_IN_PROJECT = "imported_elsewhere_in_project"
    ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY = "origin_imports_constructor_conditionally"


@dataclass(frozen=True)
class UnsafeRule:
    """A short human-readable explanation plus the docs anchor slug for one UnsafeReason."""

    message: str
    doc_anchor: str


UNSAFE_RULES: dict[UnsafeReason, UnsafeRule] = {
    UnsafeReason.PEP695_VERSION_GATE: UnsafeRule(
        "target's minimum Python version is unknown or below 3.12", "feature-typevar-modernization-pep695-version-gate",
    ),
    UnsafeReason.DECLARED_TYPEVAR_EXPORTED: UnsafeRule(
        "exported via __all__", "feature-typevar-modernization-declared-typevar-exported",
    ),
    UnsafeReason.USED_IN_GENERIC_CLASS: UnsafeRule(
        "only used inside a class that is generic over it", "feature-typevar-modernization-used-in-generic-class",
    ),
    UnsafeReason.DECLARATION_NAME_CONFLICT: UnsafeRule(
        "a name its declaration uses means something else in this file",
        "feature-typevar-modernization-declaration-name-conflict",
    ),
    UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT: UnsafeRule(
        "imported directly by another file in the target project", "feature-typevar-modernization-imported-elsewhere-in-project",
    ),
    UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY: UnsafeRule(
        "origin module imports TypeVar/ParamSpec/TypeVarTuple conditionally, e.g. per Python version",
        "feature-typevar-modernization-origin-imports-constructor-conditionally",
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


def _declares_type_param(class_node: ast.ClassDef, name: str) -> bool:
    """Return True if the class declares `name` as its own PEP 695 type parameter (`class Box[T]:`)."""
    return any(type_param_name(param) == name for param in class_node.type_params)


def _inherits_type_param(class_node: ast.ClassDef, name: str) -> bool:
    """Return True if the class is generic over the module-level `name` through one of its bases.

    That is, a base mentions `name` (`Generic[T]`, `Protocol[T]`, `Mapping[T]`, `Base[int, T]`) and the
    class doesn't declare its own `name`, which would be the one its bases refer to instead.
    """
    return not _declares_type_param(class_node, name) and any(
        isinstance(child, ast.Name) and child.id == name for base in class_node.bases for child in ast.walk(base)
    )


def declaration_argument_names(decl_stmt: ast.Assign) -> set[str]:
    """Return the non-builtin names a declaration's arguments use, e.g. {"Shape"} for `TypeVar("T", bound=Shape)`.

    The first positional argument (the type parameter's own name) is skipped; a string argument is read as a
    forward reference (`bound="Shape"`). A string that isn't a valid expression contributes no names.
    """
    call = cast("ast.Call", decl_stmt.value)
    names: set[str] = set()
    for argument in [*call.args[1:], *(keyword.value for keyword in call.keywords)]:
        expression = argument
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            try:
                expression = ast.parse(argument.value, mode="eval").body
            except SyntaxError:
                continue
        names.update(node.id for node in ast.walk(expression) if isinstance(node, ast.Name))
    return names - set(dir(builtins))


def from_import_sources(tree: ast.Module) -> dict[str, tuple[str, int] | None]:
    """Map every name bound at module level to its `from` import's (module, level), or None if bound otherwise.

    Names bound by a class, function, assignment or plain `import` map to None.
    """
    sources: dict[str, tuple[str, int] | None] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom):
            for alias in stmt.names:
                sources[alias.asname or alias.name] = (stmt.module or "", stmt.level)
        elif isinstance(stmt, ast.Import):
            for alias in stmt.names:
                sources[(alias.asname or alias.name).split(".")[0]] = None
        elif isinstance(stmt, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            sources[stmt.name] = None
        elif isinstance(stmt, ast.Assign | ast.AnnAssign):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            for target in targets:
                for node in ast.walk(target):
                    if isinstance(node, ast.Name):
                        sources[node.id] = None
    return sources


def _imports_name_conditionally(tree: ast.Module, name: str) -> bool:
    """Return True if an import inside a module-level `if`/`try` block binds `name`."""
    for stmt in tree.body:
        if not isinstance(stmt, ast.If | ast.Try | ast.TryStar):
            continue
        for node in ast.walk(stmt):
            if isinstance(node, ast.Import | ast.ImportFrom) and any(
                (alias.asname or alias.name.split(".")[0]) == name for alias in node.names
            ):
                return True
    return False


def is_safe_to_localize(origin_tree: ast.Module, name: str) -> UnsafeReason | None:
    """Return None if `name` is safe to duplicate as a local declaration, else the reason it isn't.

    Its constructor (TypeVar/ParamSpec/TypeVarTuple) must not be imported inside a module-level
    `if`/`try` block at the origin (ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY), since which
    implementation it binds then depends on the runtime, e.g. `typing_extensions` below 3.13.
    """
    declaration = find_type_param_declarations(origin_tree).get(name)
    if declaration is not None and _imports_name_conditionally(origin_tree, type_param_constructor_name(declaration)):
        return UnsafeReason.ORIGIN_IMPORTS_CONSTRUCTOR_CONDITIONALLY
    return None


def find_import_source(tree: ast.Module, name: str) -> str | None:
    """Which module a bare name (e.g. "TypeVar") was imported from in this file, e.g. "typing"."""
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module is not None:
            for alias in stmt.names:
                if (alias.asname or alias.name) == name:
                    return stmt.module
    return None


def functions_using_nodes(
    tree: ast.Module, names: Iterable[str]
) -> dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Map each of `names`, in the given order, to the outermost function/method node whose signature or body references it.

    A name referenced inside a nested function (a closure) is attributed to the *outermost*
    function in its nesting chain, never the nested one: a PEP 695 type parameter declared on the
    enclosing function is already visible inside its closures.
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


def functions_in_generic_classes(tree: ast.Module, name: str) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return every function or method defined inside a class that is generic over `name`.

    A class is generic over `name` when it declares it as a PEP 695 type parameter (`class Box[T]:`)
    or inherits it through one of its bases (see _inherits_type_param).
    """
    # TODO: try to come up with a smart solution for when Generic can be safely changed, but don't touch it for now.
    return [
        function
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and (_declares_type_param(node, name) or _inherits_type_param(node, name))
        for function in ast.walk(node)
        if isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def is_safe_to_remove(
    tree: ast.Module,
    name: str,
    project_wide_imported_names: frozenset[str] = frozenset(),
) -> UnsafeReason | None:
    """Return None if this file's own binding of `name` may be removed or replaced.

    Otherwise returns the reason it may not: DECLARED_TYPEVAR_EXPORTED if exported via `__all__`,
    or IMPORTED_ELSEWHERE_IN_PROJECT if `name` is in `project_wide_imported_names` (another file in
    the target project imports it directly, regardless of `__all__`).
    """
    dunder_all = _find_dunder_all(tree)
    if dunder_all is not None and name in dunder_all:
        return UnsafeReason.DECLARED_TYPEVAR_EXPORTED
    if name in project_wide_imported_names:
        return UnsafeReason.IMPORTED_ELSEWHERE_IN_PROJECT
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
            current = shadowed or any(type_param_name(param) == name for param in node.type_params)
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

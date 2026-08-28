import ast
from pathlib import Path
from typing import Any, cast

from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.utils.python_version import minimum_python_version

PEP_695_MINIMUM = (3, 12)


def target_supports_pep695(file_path: str) -> bool:
    """True only if the target codebase's minimum supported Python version (see
    renaissance.utils.python_version.minimum_python_version) is 3.12+. Conservative by
    design: an unknown minimum (no pyproject.toml, no/unparsable requires-python, or a
    version below 3.12) all return False - PEP 695 syntax (`def f[T](...)`) is a hard
    SyntaxError before Python 3.12, so an unknown minimum must never be treated as safe.
    """
    minimum = minimum_python_version(file_path)
    return minimum is not None and minimum >= PEP_695_MINIMUM


def _is_type_param_call(value: ast.expr) -> bool:
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


def type_param_constructor_name(decl_stmt: ast.Assign) -> str:
    """The name of the call a declaration uses, e.g. "TypeVar" for `T = TypeVar("T")`."""
    call = cast(ast.Call, decl_stmt.value)
    return cast(ast.Name, call.func).id


def _find_dunder_all(tree: ast.Module) -> set[str] | None:
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets):
            if isinstance(stmt.value, ast.List | ast.Tuple | ast.Set):
                return {
                    elt.value
                    for elt in stmt.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                }
    return None


def _used_in_exported_generic_base(tree: ast.Module, name: str) -> bool:
    # True if `name` appears inside a "Generic[...]" base of any class defined in this module
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


def is_safe_to_localize(origin_tree: ast.Module, name: str) -> bool:
    # A TypeVar is safe to localize (duplicate as a local declaration) only if the
    # origin module doesn't advertise it as public API: not re-exported via __all__,
    # and not used as a class-level Generic[...] parameter (where identity crossing
    # files can matter for subclassing).
    dunder_all = _find_dunder_all(origin_tree)
    if dunder_all is not None and name in dunder_all:
        return False
    return not _used_in_exported_generic_base(origin_tree, name)


def _find_import_source(tree: ast.Module, name: str) -> str | None:
    # Which module a bare name ("TypeVar") was imported from in this file, e.g. "typing".
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module is not None:
            for alias in stmt.names:
                if (alias.asname or alias.name) == name:
                    return stmt.module
    return None


def _resolve_sibling_module(importing_file: str, module_name: str) -> Path | None:
    # Only resolves simple "from module_name import ..." to a sibling .py file in the
    # same directory. Dotted/package imports are out of scope for this recipe.
    if "." in module_name:
        return None
    candidate = Path(importing_file).parent / f"{module_name}.py"
    return candidate if candidate.is_file() else None


def _functions_using_nodes(
    tree: ast.Module, names: set[str]
) -> dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Map each of `names` to the function/method nodes whose signature or body references it."""
    usage: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {name: [] for name in names}

    def visit(node: ast.AST, enclosing: ast.FunctionDef | ast.AsyncFunctionDef | None) -> None:
        current = enclosing
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            current = node
        if isinstance(node, ast.Name) and current is not None and node.id in usage and current not in usage[node.id]:
            usage[node.id].append(current)
        for child in ast.iter_child_nodes(node):
            visit(child, current)

    visit(tree, None)
    return usage


def _used_outside_functions(tree: ast.Module, name: str, decl_stmt: ast.Assign) -> bool:
    # True if `name` is referenced anywhere outside a function/method body - e.g. a class's
    # Generic[...] base or a module-level type alias - other than its own declaration.
    def visit(node: ast.AST, in_function: bool) -> bool:
        if node is decl_stmt:
            return False
        if isinstance(node, ast.Name) and node.id == name and not in_function:
            return True
        current = in_function or isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        return any(visit(child, current) for child in ast.iter_child_nodes(node))

    return visit(tree, False)


def is_safe_to_convert(tree: ast.Module, name: str, decl_stmt: ast.Assign) -> bool:
    # A TypeVar is safe to convert to PEP 695 syntax (and its declaration removed) only if
    # it isn't referenced anywhere outside the functions using it - a Generic[...] base or
    # a module-level type alias would break if the name disappeared.
    dunder_all = _find_dunder_all(tree)
    if dunder_all is not None and name in dunder_all:
        return False
    return not _used_outside_functions(tree, name, decl_stmt)


def _all_refs_shadowed_by_pep695(tree: ast.Module, name: str, decl_stmt: ast.Assign) -> bool:
    # True if every remaining reference to `name` sits inside a function that already
    # declares its own PEP 695 type parameter of the same name - e.g. `def b[T](x: T) -> T:`,
    # where `T` resolves to the function's own parameter, not the module-level declaration,
    # making it dead. Also true (vacuously) if `name` isn't referenced anywhere at all.
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
            current = any(param.name == name for param in node.type_params)
        for child in ast.iter_child_nodes(node):
            visit(child, current)

    visit(tree, False)
    return not found_live_use


def _build_type_param(decl_stmt: ast.Assign) -> ast.type_param:
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


def _normalize_docstring_indent(value: str, target_indent: int = 4) -> str:
    # Works around a shared rewrite-pipeline bug where a docstring's continuation lines get
    # shifted on top of their own already-correct indentation (python-ast-known-limitations.md
    # item 5). Resetting them to one canonical indent level here means the later shift lands
    # each line at the right depth instead of compounding.
    lines = value.split("\n")
    if len(lines) < 2:
        return value  # single-line docstring - nothing to double-indent, see item 5
    body = lines[1:]
    non_blank = [line for line in body if line.strip()]
    if not non_blank:
        return value
    common = min(len(line) - len(line.lstrip(" ")) for line in non_blank)
    prefix = " " * target_indent
    result = [lines[0]]
    for i, line in enumerate(body):
        content = line[common:] if common else line
        is_last = i == len(body) - 1
        # rstrip (not strip) preserves each line's own indentation *relative* to `common` -
        # e.g. a nested list inside the docstring stays nested, not flattened to one level.
        result.append(prefix + content.rstrip() if (content.strip() or is_last) else "")
    return "\n".join(result)


def _unparse_function(function: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    docstring = ast.get_docstring(function, clean=False)
    if docstring is not None and "\n" in docstring:
        cast(ast.Constant, cast(ast.Expr, function.body[0]).value).value = _normalize_docstring_indent(docstring)
    return ast.unparse(function)


class TypeVarCheck(PythonRefactoring):
    # Set directly (e.g. in a test) to skip the pyproject.toml lookup and use this value
    # instead - mirrors how `in_memory` is set on the base class after construction.
    min_python_override: tuple[int, int] | None = None

    def run(self) -> None:
        self.result = self.check()

    def _target_supports_pep695(self) -> bool:
        if self.min_python_override is not None:
            return self.min_python_override >= PEP_695_MINIMUM
        return target_supports_pep695(self.filename)

    def check(self) -> dict[str, dict[str, Any]]:
        """Check this file's TypeVar/ParamSpec/TypeVarTuple usage end to end, running three
        phases in order - localize_imported_typevars, then convert_declared_typevars, then
        remove_orphaned_declarations (see each method's own docstring for what it does and
        why). Returns {"cross_file": {...}, "converted": {...}, "orphaned": {...}}, each
        mapping name -> "fixed" | "unsafe".
        """
        cross_file = self.localize_imported_typevars()
        if "fixed" in cross_file.values():
            self.commit()

        converted = self.convert_declared_typevars()
        if "fixed" in converted.values():
            self.commit()

        orphaned = self.remove_orphaned_declarations()
        if "fixed" in orphaned.values():
            self.commit()

        return {
            "cross_file": cross_file,
            "converted": converted,
            "orphaned": orphaned,
        }

    def find_multi_scope_typevars(self) -> dict[str, set[str]]:
        # Reports names shared across 2+ functions - purely informational, since
        # convert_declared_typevars() converts and cleans up every scope regardless.
        tree = cast(ast.Module, self.root.node)
        declared_names = set(find_type_param_declarations(tree).keys())
        usage = _functions_using_nodes(tree, declared_names)
        return {name: {fn.name for fn in funcs} for name, funcs in usage.items() if len(funcs) > 1}

    def convert_declared_typevars(self) -> dict[str, str]:
        """Rewrite every function using a module-level TypeVar/ParamSpec/TypeVarTuple to
        PEP 695 generic syntax (`def f[T](...)`), whether it's used by one function or
        shared across several, then remove the now-redundant module-level declaration -
        see is_safe_to_convert and the check() docstring. Returns {name: "fixed" | "unsafe"}.

        PEP 695 syntax requires Python 3.12+ on the target codebase (see
        target_supports_pep695); if the nearest pyproject.toml's `requires-python` doesn't
        guarantee that, every candidate is reported "unsafe" and the file is left untouched
        by this phase - localize_imported_typevars still runs regardless, since it never
        introduces PEP 695 syntax.
        """
        tree = cast(ast.Module, self.root.node)
        declarations = find_type_param_declarations(tree)
        usage = _functions_using_nodes(tree, set(declarations.keys()))

        if not self._target_supports_pep695():
            return dict.fromkeys(usage, "unsafe")

        results: dict[str, str] = {}
        for name, functions in usage.items():
            decl_stmt = declarations[name]
            if not is_safe_to_convert(tree, name, decl_stmt):
                results[name] = "unsafe"
                continue

            type_param = _build_type_param(decl_stmt)
            for function in functions:
                if any(existing.name == name for existing in function.type_params):
                    continue  # already PEP 695 syntax (e.g. converted by ruff already) - don't duplicate
                function.type_params = [*function.type_params, type_param]
                self.replace(_unparse_function(function), self._find_rst_node(function), False, False)

            self._remove_declaration(decl_stmt)
            results[name] = "fixed"

        return results

    def remove_orphaned_declarations(self) -> dict[str, str]:
        """Remove a module-level TypeVar/ParamSpec/TypeVarTuple declaration once every
        remaining reference to it is shadowed by a same-named PEP 695 type parameter on
        the function(s) using it (see _all_refs_shadowed_by_pep695) - the state ruff's
        UP047 leaves behind after converting a signature, since that rule documents that
        it never removes the declaration it makes redundant. Returns {name: "fixed" | "unsafe"}.
        """
        tree = cast(ast.Module, self.root.node)
        declarations = find_type_param_declarations(tree)

        results: dict[str, str] = {}
        for name, decl_stmt in declarations.items():
            if not _all_refs_shadowed_by_pep695(tree, name, decl_stmt):
                continue

            if not is_safe_to_convert(tree, name, decl_stmt):
                results[name] = "unsafe"
                continue

            self._remove_declaration(decl_stmt)
            results[name] = "fixed"

        return results

    def _find_rst_node(self, target: ast.AST) -> Any:
        found: list[Any] = []

        def visit(node: Any) -> None:
            if node.node is target:
                found.append(node)

        self.root.process(visit)
        return found[0]

    def _remove_declaration(self, decl_stmt: ast.Assign) -> None:
        for stmt_node in self.body:
            if cast(ast.AST, stmt_node.node) is decl_stmt:
                self.remove(stmt_node)
                break
        self._remove_constructor_import_if_unused(decl_stmt)

    def _remove_constructor_import_if_unused(self, decl_stmt: ast.Assign) -> None:
        # Only drop the "from typing import TypeVar" (etc) if nothing else in the file
        # still calls it - e.g. another, unrelated TypeVar declaration.
        tree = cast(ast.Module, self.root.node)
        ctor_name = type_param_constructor_name(decl_stmt)
        still_used = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == ctor_name
            and node is not decl_stmt.value
            for node in ast.walk(tree)
        )
        if still_used:
            return

        for import_node in self.body:
            raw = cast(ast.AST, import_node.node)
            if not isinstance(raw, ast.ImportFrom) or not any((alias.asname or alias.name) == ctor_name for alias in raw.names):
                continue

            remaining = [
                alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
                for alias in raw.names
                if (alias.asname or alias.name) != ctor_name
            ]
            if remaining:
                self.replace(f"from {raw.module} import {', '.join(remaining)}", import_node, False, False)
            else:
                self.remove(import_node)
            break

    def localize_imported_typevars(self) -> dict[str, str]:
        """Find TypeVar/ParamSpec/TypeVarTuple names imported from a sibling module and,
        where safe (see is_safe_to_localize), rewrite the import into an equivalent local
        declaration. Returns {name: "fixed" | "unsafe"} for every candidate found.
        """
        results: dict[str, str] = {}

        for import_node in self.body:
            raw = cast(ast.AST, import_node.node)
            if not isinstance(raw, ast.ImportFrom) or raw.module is None or raw.level != 0:
                continue

            origin_path = _resolve_sibling_module(self.filename, raw.module)
            if origin_path is None:
                continue

            origin_tree = ast.parse(origin_path.read_text())
            declarations = find_type_param_declarations(origin_tree)

            for alias in raw.names:
                if alias.asname is not None or alias.name not in declarations:
                    continue

                if not is_safe_to_localize(origin_tree, alias.name):
                    results[alias.name] = "unsafe"
                    continue

                decl_stmt = declarations[alias.name]
                needed_import = self._missing_constructor_import(origin_tree, decl_stmt)
                self._localize_import(import_node, raw, alias.name, decl_stmt, needed_import)
                results[alias.name] = "fixed"

        return results

    def _missing_constructor_import(self, origin_tree: ast.Module, decl_stmt: ast.Assign) -> str | None:
        # The localized declaration calls TypeVar/ParamSpec/TypeVarTuple; make sure that
        # name is actually importable in the target file, or the fix produces broken code.
        ctor_name = type_param_constructor_name(decl_stmt)
        ctor_module = _find_import_source(origin_tree, ctor_name)
        if ctor_module is None:
            return None

        for import_node in self.body:
            raw = cast(ast.AST, import_node.node)
            if isinstance(raw, ast.ImportFrom) and raw.module == ctor_module:
                if any((alias.asname or alias.name) == ctor_name for alias in raw.names):
                    return None

        return f"from {ctor_module} import {ctor_name}"

    def _localize_import(
        self, import_node: Any, raw: ast.ImportFrom, name: str, decl_stmt: ast.Assign, needed_import: str | None
    ) -> None:
        decl_text = ast.unparse(decl_stmt)
        if needed_import is not None:
            decl_text = f"{needed_import}\n{decl_text}"

        remaining = [
            alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
            for alias in raw.names
            if alias.name != name
        ]

        if remaining:
            new_import = f"from {raw.module} import {', '.join(remaining)}"
            self.replace(f"{new_import}\n{decl_text}", import_node, False, False)
        else:
            self.replace(decl_text, import_node, False, False)

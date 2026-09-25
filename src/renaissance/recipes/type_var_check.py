"""Recipe that modernizes legacy TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax."""

import ast
from pathlib import Path
from typing import Any, cast

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.python_refactoring import PythonRefactoring, narrowed_import_text
from renaissance.recipes.step_runner import Step, run_steps
from renaissance.recipes.type_var_domain import (
    UnsafeReason,
    all_refs_shadowed_by_pep695,
    build_type_param,
    find_import_source,
    find_type_param_declarations,
    functions_using_nodes,
    is_safe_to_convert,
    is_safe_to_localize,
    type_param_constructor_name,
    type_param_name,
)
from renaissance.utils.import_resolution import resolve_project_module
from renaissance.utils.unparse_utils import unparse_signature_only

PEP_695_MINIMUM = (3, 12)


class TypeVarCheck(PythonRefactoring):
    """Modernize legacy TypeVar/ParamSpec/TypeVarTuple usage in a Python file to PEP 695 syntax.

    See check() for the three phases this runs, in order.
    """

    # Minimum Python version the target codebase supports; None means unknown.
    min_python: tuple[int, int] | None = None

    # Names other files in the target project import directly from this file; never removed.
    project_wide_imported_names: frozenset[str] = frozenset()

    # Root that absolute imports resolve from; None falls back to this file's own directory.
    project_root: Path | None = None

    def run(self) -> None:
        """Entry point called by PythonRefactoring.process(); stores check()'s result."""
        self.result = self.check()

    def _target_supports_pep695(self) -> bool:
        """Return True only if min_python is known and is 3.12+.

        An unknown minimum returns False: PEP 695 syntax (`def f[T](...)`) is a hard SyntaxError
        before Python 3.12.
        """
        return self.min_python is not None and self.min_python >= PEP_695_MINIMUM

    def check(self) -> dict[str, dict[str, str]]:
        """Check this file's TypeVar/ParamSpec/TypeVarTuple usage end to end.

        Runs three phases in order - localize_imported_typevars, then convert_declared_typevars,
        then remove_orphaned_declarations (see each method's own docstring for what it does and
        why). Returns {"cross_file": {...}, "converted": {...}, "orphaned": {...}}, each mapping
        name -> "fixed" | "unsafe".
        """
        return run_steps(
            [
                Step("cross_file", self, self.localize_imported_typevars),
                Step("converted", self, self.convert_declared_typevars),
                Step("orphaned", self, self.remove_orphaned_declarations),
            ],
        )

    def convert_declared_typevars(self) -> dict[str, str]:
        """Rewrite every function using a module-level TypeVar/ParamSpec/TypeVarTuple to PEP 695 syntax.

        Whether it's used by one function or shared across several, then remove the
        now-redundant module-level declaration - see is_safe_to_convert and the check()
        docstring. Returns {name: "fixed" | "unsafe"}.

        PEP 695 syntax requires Python 3.12+ on the target codebase; if min_python doesn't
        guarantee that, every candidate is reported "unsafe" and the file is left untouched
        by this phase - localize_imported_typevars still runs regardless, since it never
        introduces PEP 695 syntax. The specific UnsafeReason behind each "unsafe" entry is
        recorded on self.converted_unsafe_reasons.
        """
        root = cast("PythonRstNode", cast("object", self.root))
        tree = cast(ast.Module, root.node)
        declarations = find_type_param_declarations(tree)
        usage = functions_using_nodes(tree, set(declarations.keys()))

        if not self._target_supports_pep695():
            self.converted_unsafe_reasons = dict.fromkeys(usage, UnsafeReason.PEP695_VERSION_GATE)
            return dict.fromkeys(usage, "unsafe")

        results: dict[str, str] = {}
        self.converted_unsafe_reasons: dict[str, UnsafeReason] = {}
        # Collected here instead of replaced immediately: a function using 2+ converted type
        # params (e.g. TypeVar and ParamSpec) must get exactly one self.replace() covering all
        # of them - queuing one per name would target the same function node twice before a
        # commit, which the rewriter rejects as conflicting.
        touched_functions: dict[int, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        for name, functions in usage.items():
            decl_stmt = declarations[name]
            reason = is_safe_to_convert(tree, name, decl_stmt, self.project_wide_imported_names)
            if reason is not None:
                self._mark_unsafe(results, self.converted_unsafe_reasons, name, reason)
                continue

            type_param = build_type_param(decl_stmt)
            for function in functions:
                if any(type_param_name(existing) == name for existing in function.type_params):
                    continue  # already PEP 695 syntax (handled by Ruff)
                function.type_params = [*function.type_params, type_param]
                touched_functions[id(function)] = function

            self._remove_declaration(decl_stmt)
            results[name] = "fixed"

        for function in touched_functions.values():
            rst_node = self.find_rst_node(function)
            self.replace(unparse_signature_only(function, rst_node.text), rst_node, False, False)

        return results

    def remove_orphaned_declarations(self) -> dict[str, str]:
        """Remove a module-level TypeVar/ParamSpec/TypeVarTuple declaration once it's orphaned.

        Every remaining reference to it is shadowed by a same-named PEP 695 type parameter on
        the function(s) using it (see all_refs_shadowed_by_pep695) - the state ruff's UP047
        leaves behind after converting a signature, since that rule documents that it never
        removes the declaration it makes redundant. Returns {name: "fixed" | "unsafe"}; the
        specific UnsafeReason behind each "unsafe" entry is recorded on
        self.orphaned_unsafe_reasons.
        """
        root = cast("PythonRstNode", cast("object", self.root))
        tree = cast(ast.Module, root.node)
        declarations = find_type_param_declarations(tree)

        results: dict[str, str] = {}
        self.orphaned_unsafe_reasons: dict[str, UnsafeReason] = {}
        for name, decl_stmt in declarations.items():
            if not all_refs_shadowed_by_pep695(tree, name, decl_stmt):
                continue

            reason = is_safe_to_convert(tree, name, decl_stmt, self.project_wide_imported_names)
            if reason is not None:
                self._mark_unsafe(results, self.orphaned_unsafe_reasons, name, reason)
                continue

            self._remove_declaration(decl_stmt)
            results[name] = "fixed"

        return results

    def _mark_unsafe(self, results: dict[str, str], reasons: dict[str, UnsafeReason], name: str, reason: UnsafeReason) -> None:
        """Record `name` as unsafe with `reason` in both `results` (status) and `reasons` (why)."""
        results[name] = "unsafe"
        reasons[name] = reason

    def _remove_declaration(self, decl_stmt: ast.Assign) -> None:
        """Remove decl_stmt's statement from the file."""
        for stmt_node in self.body:
            if stmt_node.node is decl_stmt:
                # TODO - enable once comment blocks get correctly deleted
                self.remove(stmt_node, include_comments=False)
                break

    def localize_imported_typevars(self) -> dict[str, str]:
        """Find TypeVar/ParamSpec/TypeVarTuple names imported from anywhere in the target project.

        Absolute and relative imports are resolved against project_root. Where safe (see
        is_safe_to_localize), rewrites the import into an equivalent local
        declaration. Returns {name: "fixed" | "unsafe"} for every candidate found; the specific
        UnsafeReason behind each "unsafe" entry is recorded on self.cross_file_unsafe_reasons.
        """
        results: dict[str, str] = {}
        self.cross_file_unsafe_reasons: dict[str, UnsafeReason] = {}

        project_root = self.project_root if self.project_root is not None else Path(self.filename).parent
        for import_node in self.body:
            raw = import_node.node
            if not isinstance(raw, ast.ImportFrom):
                continue

            origin_path = resolve_project_module(Path(self.filename), project_root, raw.module, raw.level)
            if origin_path is None:
                continue

            origin_tree = ast.parse(origin_path.read_text(encoding="utf-8"))
            declarations = find_type_param_declarations(origin_tree)

            for alias in raw.names:
                if alias.asname is not None or alias.name not in declarations:
                    continue

                reason = is_safe_to_localize(origin_tree, alias.name)
                if reason is not None:
                    self._mark_unsafe(results, self.cross_file_unsafe_reasons, alias.name, reason)
                    continue

                decl_stmt = declarations[alias.name]
                needed_import = self._missing_constructor_import(origin_tree, decl_stmt)
                self._localize_import(import_node, raw, alias.name, decl_stmt, needed_import)
                results[alias.name] = "fixed"

        return results

    def _missing_constructor_import(self, origin_tree: ast.Module, decl_stmt: ast.Assign) -> str | None:
        """Build the "from module import Ctor" text so the localized declaration's constructor is importable.

        Prepend this to the declaration if the constructor call (TypeVar/ParamSpec/TypeVarTuple)
        isn't already imported here; returns None if it already is.
        """
        ctor_name = type_param_constructor_name(decl_stmt)
        ctor_module = find_import_source(origin_tree, ctor_name)
        if ctor_module is None:
            return None

        for import_node in self.body:
            raw = import_node.node
            if (
                isinstance(raw, ast.ImportFrom)
                and raw.module == ctor_module
                and any((alias.asname or alias.name) == ctor_name for alias in raw.names)
            ):
                return None

        return f"from {ctor_module} import {ctor_name}"

    def _localize_import(self, import_node: Any, raw: ast.ImportFrom, name: str, decl_stmt: ast.Assign, needed_import: str | None) -> None:
        """Replace import_node with decl_stmt's text as a local declaration.

        Narrows or removes the original import for name, and prepends needed_import if the
        declaration's constructor isn't already imported here.
        """
        decl_text = ast.unparse(decl_stmt)
        if needed_import is not None:
            decl_text = f"{needed_import}\n{decl_text}"

        new_import = narrowed_import_text(raw, name)
        if new_import is not None:
            self.replace(f"{new_import}\n{decl_text}", import_node, False, False)
        else:
            self.replace(decl_text, import_node, False, False)

"""Recipe that modernizes legacy TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax."""

import ast
from pathlib import Path
from typing import cast

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.python_refactoring import PythonRefactoring, narrowed_import_text
from renaissance.recipes.step_runner import Step, run_steps
from renaissance.recipes.type_var_domain import (
    UnsafeReason,
    all_refs_shadowed_by_pep695,
    build_type_param,
    declaration_argument_names,
    declared_default,
    find_type_param_declarations,
    from_import_sources,
    functions_in_generic_classes,
    functions_using_nodes,
    has_unconvertible_argument,
    is_safe_to_localize,
    is_safe_to_remove,
    type_param_constructor_name,
    type_param_name,
    type_params_defaults_last,
)
from renaissance.utils.import_resolution import rebase_relative_module, resolve_project_module
from renaissance.utils.unparse_utils import unparse_signature_only

PEP_695_MINIMUM = (3, 12)
PEP_696_MINIMUM = (3, 13)


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
        """Return True only if min_python is known and is 3.12+, where PEP 695 syntax (`def f[T](...)`) exists."""
        return self.min_python is not None and self.min_python >= PEP_695_MINIMUM

    def _target_supports_pep696(self) -> bool:
        """Return True only if min_python is known and is 3.13+, where PEP 696 defaults (`def f[T = int](...)`) exist."""
        return self.min_python is not None and self.min_python >= PEP_696_MINIMUM

    def _conversion_refusal(self, decl_stmt: ast.Assign) -> UnsafeReason | None:
        """Return why decl_stmt can't be converted to a PEP 695 type parameter on this target, or None if it can."""
        if not self._target_supports_pep695():
            return UnsafeReason.PEP695_VERSION_GATE
        if has_unconvertible_argument(decl_stmt):
            return UnsafeReason.NO_PEP695_EQUIVALENT
        if declared_default(decl_stmt) is not None and not self._target_supports_pep696():
            return UnsafeReason.PEP696_VERSION_GATE
        return None

    def check(self) -> dict[str, dict[str, str]]:
        """Run the three phases in order, committing each one that fixed something.

        localize_imported_typevars, then convert_declared_typevars, then
        remove_orphaned_declarations. Returns {"cross_file": {...}, "converted": {...},
        "orphaned": {...}}, each mapping name -> "fixed" | "unsafe".
        """
        return run_steps(
            [
                Step("cross_file", self, self.localize_imported_typevars),
                Step("converted", self, self.convert_declared_typevars),
                Step("orphaned", self, self.remove_orphaned_declarations),
            ],
        )

    def convert_declared_typevars(self) -> dict[str, str]:
        """Add a PEP 695 type parameter to every function using a module-level TypeVar/ParamSpec/TypeVarTuple.

        The declaration is left in place. Names whose references are all shadowed by a same-named PEP 695
        type parameter are skipped, and methods of a class generic over the name are never converted.
        Bounds, constraints and `default=` are carried over, with defaulted type parameters placed last.
        A name only such methods use, or whose declaration _conversion_refusal rejects, is reported
        "unsafe", with its UnsafeReason on self.converted_unsafe_reasons. Returns {name: "fixed" | "unsafe"}.
        """
        root = cast("PythonRstNode", cast("object", self.root))
        tree = cast("ast.Module", root.node)
        declarations = find_type_param_declarations(tree)
        usage = functions_using_nodes(tree, declarations.keys())

        results: dict[str, str] = {}
        self.converted_unsafe_reasons: dict[str, UnsafeReason] = {}
        # One self.replace() per function: a function using two converted names would otherwise get two
        # rewrites of the same node, which the rewriter rejects as conflicting.
        touched_functions: dict[int, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        for name, functions in usage.items():
            decl_stmt = declarations[name]
            if all_refs_shadowed_by_pep695(tree, name, decl_stmt):
                continue

            generic_class_method_ids = {id(method) for method in functions_in_generic_classes(tree, name)}
            candidates = [
                function
                for function in functions
                if id(function) not in generic_class_method_ids
                and not any(type_param_name(existing) == name for existing in function.type_params)
            ]
            if not candidates:
                if any(id(function) in generic_class_method_ids for function in functions):
                    self._mark_unsafe(results, self.converted_unsafe_reasons, name, UnsafeReason.USED_IN_GENERIC_CLASS)
                continue
            reason = self._conversion_refusal(decl_stmt)
            if reason is not None:
                self._mark_unsafe(results, self.converted_unsafe_reasons, name, reason)
                continue

            type_param = build_type_param(decl_stmt)
            for function in candidates:
                function.type_params = [*function.type_params, type_param]
                touched_functions[id(function)] = function
            results[name] = "fixed"

        for function in touched_functions.values():
            function.type_params = type_params_defaults_last(function.type_params)
            rst_node = self.find_rst_node(function)
            self.replace(unparse_signature_only(function, rst_node.text), rst_node, include_whitespace=False, include_comments=False)

        return results

    def remove_orphaned_declarations(self) -> dict[str, str]:
        """Remove every module-level TypeVar/ParamSpec/TypeVarTuple declaration that nothing uses anymore.

        A declaration is orphaned when no reference to its name remains outside a same-named PEP 695 type
        parameter (see all_refs_shadowed_by_pep695). One that is_safe_to_remove rejects is kept and
        reported "unsafe", with its UnsafeReason on self.orphaned_unsafe_reasons. Returns
        {name: "fixed" | "unsafe"}.
        """
        root = cast("PythonRstNode", cast("object", self.root))
        tree = cast("ast.Module", root.node)

        results: dict[str, str] = {}
        self.orphaned_unsafe_reasons: dict[str, UnsafeReason] = {}
        for name, decl_stmt in find_type_param_declarations(tree).items():
            if not all_refs_shadowed_by_pep695(tree, name, decl_stmt):
                continue

            # TODO: a public TypeVar no file in the project uses (e.g. redis.typing.AnyKeyT) is removed,
            # though other projects may import it.
            reason = is_safe_to_remove(tree, name, self.project_wide_imported_names)
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
        """Replace imports of TypeVar/ParamSpec/TypeVarTuple names from the target project with local declarations.

        Imports are resolved against project_root. Where safe, the import becomes a copy of the origin's
        declaration, plus imports from the origin for the names its arguments use (e.g. `bound=Shape`).
        It is unsafe when is_safe_to_localize rejects the origin or _argument_names_to_import returns None.
        Returns {name: "fixed" | "unsafe"}, with each UnsafeReason on self.cross_file_unsafe_reasons.
        """
        results: dict[str, str] = {}
        self.cross_file_unsafe_reasons: dict[str, UnsafeReason] = {}
        importing_tree = cast("ast.Module", cast("PythonRstNode", cast("object", self.root)).node)

        project_root = self.project_root if self.project_root is not None else Path(self.filename).parent
        for import_node in self.body:
            raw = import_node.node
            if not isinstance(raw, ast.ImportFrom):
                continue

            origin_path = resolve_project_module(Path(self.filename), project_root, raw.module, raw.level)
            if origin_path is None:
                continue

            self._localize_names_from(import_node, raw, importing_tree, origin_path, results)

        return results

    def _localize_names_from(
        self,
        import_node: PythonRstNode,
        raw: ast.ImportFrom,
        importing_tree: ast.Module,
        origin_path: Path,
        results: dict[str, str],
    ) -> None:
        """Localize every safe type parameter name that raw imports from the origin_path file, in one edit of import_node.

        Records each name in results as "fixed" or, via _mark_unsafe, as "unsafe".
        """
        origin_tree = ast.parse(origin_path.read_text(encoding="utf-8"), str(origin_path))
        declarations = find_type_param_declarations(origin_tree)
        localized: dict[str, ast.Assign] = {}
        needed_imports: list[str] = []
        needed_argument_names: set[str] = set()

        for alias in raw.names:
            # TODO: `from x import T as U` is not currently being caught, tbd
            if alias.asname is not None or alias.name not in declarations:
                continue

            decl_stmt = declarations[alias.name]
            reason = is_safe_to_localize(origin_tree, alias.name)
            if reason is not None:
                self._mark_unsafe(results, self.cross_file_unsafe_reasons, alias.name, reason)
                continue
            argument_names = self._argument_names_to_import(importing_tree, origin_tree, raw, decl_stmt)
            if argument_names is None:
                self._mark_unsafe(results, self.cross_file_unsafe_reasons, alias.name, UnsafeReason.DECLARATION_NAME_UNAVAILABLE)
                continue

            constructor_import = self._missing_constructor_import(origin_tree, origin_path, raw, decl_stmt)
            if constructor_import is not None and constructor_import not in needed_imports:
                needed_imports.append(constructor_import)
            needed_argument_names |= argument_names
            localized[alias.name] = decl_stmt
            results[alias.name] = "fixed"

        if not localized:
            return
        if needed_argument_names:
            needed_imports.append(f"from {'.' * raw.level}{raw.module or ''} import {', '.join(sorted(needed_argument_names))}")
        self._localize_import(import_node, raw, localized, needed_imports)

    def _missing_constructor_import(
        self,
        origin_tree: ast.Module,
        origin_path: Path,
        via: ast.ImportFrom,
        decl_stmt: ast.Assign,
    ) -> str | None:
        """Return the "from module import Ctor" line the localized declaration needs, or None if this file has it.

        The module is the one the origin imports the constructor from, as named from this file, which
        reaches the origin (origin_path) through via. If this file can't name that module, the
        constructor is imported from the origin module itself.
        """
        ctor_name = type_param_constructor_name(decl_stmt)
        ctor_source = from_import_sources(origin_tree).get(ctor_name)
        if ctor_source is None:
            # TODO: an origin using `from typing import *` lands here,
            # so a file not importing the constructor itself gets a NameError.
            # TBD - needs a fix
            return None

        via_module = "." * via.level + (via.module or "")
        ctor_module = rebase_relative_module(via.module, via.level, origin_path, ctor_source[0] or None, ctor_source[1]) or via_module

        # TODO: the constructor already imported here from another module (e.g. `typing` vs the origin's
        # `typing_extensions`) isn't matched, so a second, shadowing import of the same name is added.
        for import_node in self.body:
            raw = import_node.node
            if (
                isinstance(raw, ast.ImportFrom)
                and "." * raw.level + (raw.module or "") == ctor_module
                and any((alias.asname or alias.name) == ctor_name for alias in raw.names)
            ):
                return None

        return f"from {ctor_module} import {ctor_name}"

    def _argument_names_to_import(
        self, importing_tree: ast.Module, origin_tree: ast.Module, raw: ast.ImportFrom, decl_stmt: ast.Assign
    ) -> set[str] | None:
        """Return the names decl_stmt's arguments use that this file must import from the origin module.

        A name this file already imports from the origin module (or from the same absolute module the
        origin imports it from) is fine and not returned. Returns None if one of those names can't be
        imported from the origin as the same object: the origin doesn't bind it at module level at
        runtime (e.g. only under `if TYPE_CHECKING:`), or this file binds it to something else.
        """
        origin_sources = from_import_sources(origin_tree)
        importing_sources = from_import_sources(importing_tree)
        missing: set[str] = set()
        for name in declaration_argument_names(decl_stmt):
            if name not in origin_sources:
                return None
            if name not in importing_sources:
                missing.add(name)
                continue
            origin_source = origin_sources[name]
            accepted = {(raw.module or "", raw.level)}
            if origin_source is not None and origin_source[1] == 0:
                accepted.add(origin_source)
            if importing_sources[name] not in accepted:
                return None
        return missing

    def _localize_import(
        self,
        import_node: PythonRstNode,
        raw: ast.ImportFrom,
        declarations: dict[str, ast.Assign],
        needed_imports: list[str],
    ) -> None:
        """Replace import_node with the text of declarations' statements as local declarations, in one edit.

        Narrows or removes the original import for declarations' names, and prepends needed_imports: the
        imports the declarations need (their constructors, names their arguments use) that this file
        doesn't have yet.
        """
        decl_text = "\n".join([*needed_imports, *(ast.unparse(decl_stmt) for decl_stmt in declarations.values())])

        new_import = narrowed_import_text(raw, set(declarations))
        if new_import is not None:
            self.replace(f"{new_import}\n{decl_text}", import_node, include_whitespace=False, include_comments=False)
        else:
            self.replace(decl_text, import_node, include_whitespace=False, include_comments=False)

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Recipe that modernizes legacy TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax."""

from collections.abc import Sequence
from pathlib import Path
from typing import cast

import libcst as cst

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.step_runner import Step, run_steps
from renaissance.recipes.type_var_domain import (
    UnsafeReason,
    declaration_argument_names,
    declared_default,
    declares_type_param,
    find_type_param_declarations,
    from_import_sources,
    generic_classes,
    has_unconvertible_argument,
    is_safe_to_localize,
    is_safe_to_remove,
    module_statements,
    outermost_function,
    type_param_constructor_name,
    type_param_text,
    type_params_bracket,
    uses_of,
)
from renaissance.utils.import_resolution import import_from_module, imported_name, rebase_relative_module, resolve_project_module

PEP_695_MINIMUM = (3, 12)
PEP_696_MINIMUM = (3, 13)


class TypeVarCheck(PythonRefactoring[PythonCstNode]):
    """Modernize legacy TypeVar/ParamSpec/TypeVarTuple usage in a Python file to PEP 695 syntax.

    See check() for the three phases this runs, in order.
    """

    # Minimum Python version the target codebase supports; None means unknown.
    min_python: tuple[int, int] | None = None

    # Names other files in the target project import directly from this file; never removed.
    project_wide_imported_names: frozenset[str] = frozenset()

    # Root that absolute imports resolve from; None falls back to this file's own directory.
    project_root: Path | None = None

    def __init__(self, file: Path) -> None:
        """Prepare the recipe for file, parsed with the CST backend."""
        super().__init__(file, PythonCstNode)

    def run(self) -> None:
        """Entry point called by PythonRefactoring.process(); stores check()'s result."""
        self.result = self.check()

    def _cst_root(self) -> PythonCstNode:
        """Return the root node of the file as it currently is (after the last commit)."""
        return cast("PythonCstNode", cast("object", self.root))

    def _target_supports_pep695(self) -> bool:
        """Return True only if min_python is known and is 3.12+, where PEP 695 syntax (`def f[T](...)`) exists."""
        return self.min_python is not None and self.min_python >= PEP_695_MINIMUM

    def _target_supports_pep696(self) -> bool:
        """Return True only if min_python is known and is 3.13+, where PEP 696 defaults (`def f[T = int](...)`) exist."""
        return self.min_python is not None and self.min_python >= PEP_696_MINIMUM

    def _conversion_refusal(self, decl_stmt: cst.Assign) -> UnsafeReason | None:
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

        The declaration is left in place. A use is attributed to the outermost function containing it; a `T`
        that a same-named PEP 695 type parameter of a function or class declares is not a use. Methods of a
        class generic over the name are never converted. Bounds, constraints and `default=` are carried over
        in their original formatting, with defaulted type parameters placed last. A name only such methods
        use, or whose declaration _conversion_refusal rejects, is reported "unsafe", with its UnsafeReason on
        self.converted_unsafe_reasons. Returns {name: "fixed" | "unsafe"}.
        """
        root = self._cst_root()
        module = root.translation_unit.atu

        results: dict[str, str] = {}
        self.converted_unsafe_reasons: dict[str, UnsafeReason] = {}
        # One self.replace() per function: a function using two converted names would otherwise get two
        # rewrites of the same node, which the rewriter rejects as conflicting.
        new_params: dict[int, tuple[PythonCstNode, list[tuple[str, bool]]]] = {}
        for name, decl_stmt in find_type_param_declarations(module).items():
            uses = uses_of(root, name, decl_stmt)
            functions = list(dict.fromkeys(function for use in uses if (function := outermost_function(use)) is not None))
            if not functions:
                continue

            classes = generic_classes(uses)
            in_generic_class = [function for function in functions if self._is_inside(function, classes)]
            candidates = [
                function
                for function in functions
                if function not in in_generic_class and not declares_type_param(cast("cst.FunctionDef", function.node), name)
            ]
            if not candidates:
                if in_generic_class:
                    self._mark_unsafe(results, self.converted_unsafe_reasons, name, UnsafeReason.USED_IN_GENERIC_CLASS)
                continue
            reason = self._conversion_refusal(decl_stmt)
            if reason is not None:
                self._mark_unsafe(results, self.converted_unsafe_reasons, name, reason)
                continue

            param = (type_param_text(decl_stmt, module), declared_default(decl_stmt) is not None)
            for function in candidates:
                new_params.setdefault(id(function), (function, []))[1].append(param)
            results[name] = "fixed"

        for function, params in new_params.values():
            self._add_type_params(function, params)

        return results

    @staticmethod
    def _is_inside(node: PythonCstNode, containers: Sequence[PythonCstNode]) -> bool:
        """Return True if one of containers encloses node."""
        current = node.parent
        while current is not None:
            if any(current is container for container in containers):
                return True
            current = current.parent
        return False

    def _add_type_params(self, function: PythonCstNode, params: list[tuple[str, bool]]) -> None:
        """Add params, given as (text, has_default), to function's PEP 695 type parameters, changing nothing else.

        A function without a bracket gets one after its name; an existing bracket is rewritten with its own
        type parameters followed by params, the defaulted ones last.
        """
        node = cast("cst.FunctionDef", function.node)
        unit = function.translation_unit
        existing = node.type_parameters
        if existing is None:
            self.replace(
                node.name.value + type_params_bracket(params), unit.wrappers[node.name], include_whitespace=False, include_comments=False
            )
            return
        # TODO(FrancescoPezzella): rebuilding the existing bracket drops its comments and line breaks.
        #  https://github.com/TNO/Renaissance.Py/issues/279
        current = [
            (unit.atu.code_for_node(param.with_changes(comma=cst.MaybeSentinel.DEFAULT)), param.default is not None)
            for param in existing.params
        ]
        self.replace(type_params_bracket([*current, *params]), unit.wrappers[existing], include_whitespace=False, include_comments=False)

    def remove_orphaned_declarations(self) -> dict[str, str]:
        """Remove every module-level TypeVar/ParamSpec/TypeVarTuple declaration that nothing uses anymore.

        A declaration is orphaned when uses_of finds no use of its name: every `T` left belongs to a PEP 695
        type parameter, or there is none. One that is_safe_to_remove rejects is kept and reported "unsafe",
        with its UnsafeReason on self.orphaned_unsafe_reasons. Returns {name: "fixed" | "unsafe"}.
        """
        root = self._cst_root()
        module = root.translation_unit.atu

        results: dict[str, str] = {}
        self.orphaned_unsafe_reasons: dict[str, UnsafeReason] = {}
        for name, decl_stmt in find_type_param_declarations(module).items():
            if uses_of(root, name, decl_stmt):
                continue

            # TODO(FrancescoPezzella): a public TypeVar no file in the project uses (e.g. redis.typing.AnyKeyT) is removed,
            #  though other projects may import it.
            #  https://github.com/TNO/Renaissance.Py/issues/279
            reason = is_safe_to_remove(module, name, self.project_wide_imported_names)
            if reason is not None:
                self._mark_unsafe(results, self.orphaned_unsafe_reasons, name, reason)
                continue

            # TODO(FrancescoPezzella): `T = U = TypeVar("T")` is removed whole when T is unused, so U is no longer defined.
            #  https://github.com/TNO/Renaissance.Py/issues/279
            self._remove_declaration(decl_stmt)
            results[name] = "fixed"

        return results

    def _mark_unsafe(self, results: dict[str, str], reasons: dict[str, UnsafeReason], name: str, reason: UnsafeReason) -> None:
        """Record `name` as unsafe with `reason` in both `results` (status) and `reasons` (why)."""
        results[name] = "unsafe"
        reasons[name] = reason

    def _remove_declaration(self, decl_stmt: cst.Assign) -> None:
        """Remove decl_stmt's statement from the file."""
        # TODO(FrancescoPezzella): enable once comment blocks get correctly deleted
        #  https://github.com/TNO/Renaissance.Py/issues/189
        # TODO(FrancescoPezzella): a declaration that starts a `;` line leaves a leading `;`, a syntax error that commit()
        #  writes to disk.
        #  https://github.com/TNO/Renaissance.Py/issues/279
        self.remove(self._cst_root().translation_unit.wrappers[decl_stmt], include_comments=False)

    def localize_imported_typevars(self) -> dict[str, str]:
        """Replace imports of TypeVar/ParamSpec/TypeVarTuple names from the target project with local declarations.

        Imports are resolved against project_root. Where safe, the import becomes a copy of the origin's
        declaration, plus imports from the origin for the names its arguments use (e.g. `bound=Shape`).
        It is unsafe when is_safe_to_localize rejects the origin or _argument_names_to_import returns None.
        Returns {name: "fixed" | "unsafe"}, with each UnsafeReason on self.cross_file_unsafe_reasons.
        """
        results: dict[str, str] = {}
        self.cross_file_unsafe_reasons: dict[str, UnsafeReason] = {}
        module = self._cst_root().translation_unit.atu

        project_root = self.project_root if self.project_root is not None else Path(self.filename).parent
        for line in module.body:
            if not isinstance(line, cst.SimpleStatementLine):
                continue
            for statement in line.body:
                if not isinstance(statement, cst.ImportFrom):
                    continue
                origin_path = resolve_project_module(
                    Path(self.filename), project_root, import_from_module(statement), len(statement.relative)
                )
                if origin_path is None:
                    continue
                self._localize_names_from(line, statement, origin_path, results)

        return results

    def _localize_names_from(
        self,
        line: cst.SimpleStatementLine,
        raw: cst.ImportFrom,
        origin_path: Path,
        results: dict[str, str],
    ) -> None:
        """Localize every safe type parameter name that raw, on line, imports from the origin_path file.

        Records each name in results as "fixed" or, via _mark_unsafe, as "unsafe".

        Raises:
            SyntaxError: if the origin file can't be parsed, with the origin's path as its filename.

        """
        if isinstance(raw.names, cst.ImportStar):
            return
        try:
            origin = cst.parse_module(origin_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError as error:
            raise SyntaxError(error.message, (str(origin_path), error.raw_line, error.raw_column + 1, None)) from error
        declarations = find_type_param_declarations(origin)
        localized: dict[str, cst.Assign] = {}
        needed_imports: list[str] = []
        needed_argument_names: set[str] = set()

        for alias in raw.names:
            # TODO(FrancescoPezzella): `from x import T as U` is not currently being caught, tbd
            #  https://github.com/TNO/Renaissance.Py/issues/279
            name = alias.evaluated_name
            if alias.asname is not None or name not in declarations:
                continue

            decl_stmt = declarations[name]
            reason = is_safe_to_localize(origin, name)
            if reason is not None:
                self._mark_unsafe(results, self.cross_file_unsafe_reasons, name, reason)
                continue
            argument_names = self._argument_names_to_import(origin, raw, decl_stmt)
            if argument_names is None:
                self._mark_unsafe(results, self.cross_file_unsafe_reasons, name, UnsafeReason.DECLARATION_NAME_UNAVAILABLE)
                continue

            constructor_import = self._missing_constructor_import(origin, origin_path, raw, decl_stmt)
            if constructor_import is not None and constructor_import not in needed_imports:
                needed_imports.append(constructor_import)
            needed_argument_names |= argument_names
            localized[name] = decl_stmt
            results[name] = "fixed"

        if not localized:
            return
        if needed_argument_names:
            needed_imports.append(f"from {self._import_from_text(raw)} import {', '.join(sorted(needed_argument_names))}")
        self._localize_import(line, raw, origin, localized, needed_imports)

    @staticmethod
    def _import_from_text(raw: cst.ImportFrom) -> str:
        """Return what follows `from` in raw: its leading dots and dotted module, e.g. "..pkg.mod"."""
        return "." * len(raw.relative) + (import_from_module(raw) or "")

    def _missing_constructor_import(
        self,
        origin: cst.Module,
        origin_path: Path,
        via: cst.ImportFrom,
        decl_stmt: cst.Assign,
    ) -> str | None:
        """Return the "from module import Ctor" line the localized declaration needs, or None if this file has it.

        The module is the one the origin imports the constructor from, as named from this file, which
        reaches the origin (origin_path) through via. If this file can't name that module, the
        constructor is imported from the origin module itself.
        """
        ctor_name = type_param_constructor_name(decl_stmt)
        ctor_source = from_import_sources(origin).get(ctor_name)
        if ctor_source is None:
            # TODO(FrancescoPezzella): an origin using `from typing import *` lands here,
            #  so a file not importing the constructor itself gets a NameError.
            #  TBD - needs a fix
            #  https://github.com/TNO/Renaissance.Py/issues/279
            return None

        via_module = import_from_module(via)
        ctor_module = rebase_relative_module(via_module, len(via.relative), origin_path, ctor_source[0] or None, ctor_source[1])
        ctor_module = ctor_module or self._import_from_text(via)

        # TODO(FrancescoPezzella): the constructor already imported here from another module (e.g. `typing` vs the origin's
        #  `typing_extensions`) isn't matched, so a second, shadowing import of the same name is added.
        #  https://github.com/TNO/Renaissance.Py/issues/279
        for statement in module_statements(self._cst_root().translation_unit.atu):
            if (
                isinstance(statement, cst.ImportFrom)
                and not isinstance(statement.names, cst.ImportStar)
                and self._import_from_text(statement) == ctor_module
                and any(imported_name(alias) == ctor_name for alias in statement.names)
            ):
                return None

        return f"from {ctor_module} import {ctor_name}"

    def _argument_names_to_import(self, origin: cst.Module, raw: cst.ImportFrom, decl_stmt: cst.Assign) -> set[str] | None:
        """Return the names decl_stmt's arguments use that this file must import from the origin module.

        A name this file already imports from the origin module (or from the same absolute module the
        origin imports it from) is fine and not returned. Returns None if one of those names can't be
        imported from the origin as the same object: the origin doesn't bind it at module level at
        runtime (e.g. only under `if TYPE_CHECKING:`), or this file binds it to something else.
        """
        origin_sources = from_import_sources(origin)
        importing_sources = from_import_sources(self._cst_root().translation_unit.atu)
        missing: set[str] = set()
        for name in declaration_argument_names(decl_stmt):
            if name not in origin_sources:
                return None
            if name not in importing_sources:
                missing.add(name)
                continue
            origin_source = origin_sources[name]
            accepted = {(import_from_module(raw) or "", len(raw.relative))}
            if origin_source is not None and origin_source[1] == 0:
                accepted.add(origin_source)
            if importing_sources[name] not in accepted:
                return None
        return missing

    def _localize_import(
        self,
        line: cst.SimpleStatementLine,
        raw: cst.ImportFrom,
        origin: cst.Module,
        declarations: dict[str, cst.Assign],
        needed_imports: list[str],
    ) -> None:
        """Replace the import raw, on line, with local copies of declarations from the origin module.

        The declarations keep their original formatting and come after needed_imports: the imports they need
        (their constructors, names their arguments use) that this file doesn't have yet. If raw imports other
        names too, it is narrowed to those, keeping its comments, and the declarations go after line;
        otherwise they replace raw.
        """
        no_semicolon = cst.MaybeSentinel.DEFAULT
        decl_text = "\n".join(
            [*needed_imports, *(origin.code_for_node(decl.with_changes(semicolon=no_semicolon)) for decl in declarations.values())]
        )
        wrappers = self._cst_root().translation_unit.wrappers

        kept = [alias for alias in cast("Sequence[cst.ImportAlias]", raw.names) if imported_name(alias) not in declarations]
        if not kept:
            self.replace(decl_text, wrappers[raw], include_whitespace=False, include_comments=False)
            return
        if raw.rpar is None:
            # Without parentheses, a trailing comma after the last name is a syntax error.
            kept[-1] = kept[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        narrowed = self._cst_root().translation_unit.atu.code_for_node(raw.with_changes(names=kept, semicolon=no_semicolon))
        self.replace(narrowed, wrappers[raw], include_whitespace=False, include_comments=False)
        self.insert_after(f"\n{decl_text}", wrappers[line], include_whitespace=False, include_comments=True)

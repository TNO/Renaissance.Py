# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Recipe that modernizes legacy TypeVar/ParamSpec/TypeVarTuple usage to PEP 695 syntax."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import libcst as cst

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.step_runner import Step, run_steps
from renaissance.recipes.type_var_domain import (
    UnsafeReason,
    declaration_argument_names,
    declaration_text,
    declared_default,
    declares_type_param,
    find_type_param_declarations,
    from_import_binding,
    from_import_sources,
    generic_classes,
    has_unconvertible_argument,
    is_safe_to_localize,
    is_safe_to_remove,
    module_statements,
    names_read_by,
    owning_function,
    signature_function,
    trailing_of_sole_statement,
    type_param_constructor_name,
    type_param_text,
    type_params_bracket,
    uses_of,
)
from renaissance.utils.import_resolution import import_from_module, imported_name, rebase_relative_module, resolve_project_module

PEP_695_MINIMUM = (3, 12)
PEP_696_MINIMUM = (3, 13)


@dataclass(frozen=True)
class _Localization:
    """The type parameter names one import statement brings in that are localized, and the text that replaces them."""

    line: cst.SimpleStatementLine
    raw: cst.ImportFrom
    names: frozenset[str]
    kept: list[cst.ImportAlias]
    imports: list[str]
    declarations: list[str]


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
        """Prepare the recipe for file, parsed with the CST backend.

        type_param_kinds maps each type parameter name the phases see to "TypeVar", "ParamSpec" or "TypeVarTuple".
        """
        super().__init__(file, PythonCstNode)
        self.type_param_kinds: dict[str, str] = {}

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

        The declaration is left in place. A use is attributed to the outermost enclosing function whose signature
        uses the name; a use outside every such signature is not attributed. A `T` that a same-named PEP 695 type
        parameter of a function or class declares is not a use. Methods of a class generic over the name are never
        converted. A function that also uses a name whose declaration _conversion_refusal rejects is left unchanged,
        so no function mixes legacy and PEP 695 type parameters. Bounds, constraints and `default=` are carried over
        in their original formatting, with defaulted type parameters placed last. A name only methods of such a class
        use, whose declaration is rejected, or whose every function is left unchanged is reported "unsafe", with its
        UnsafeReason on self.converted_unsafe_reasons. Records each declaration's kind on self.type_param_kinds.
        Returns {name: "fixed" | "unsafe"}.
        """
        root = self._cst_root()
        module = root.translation_unit.atu

        results: dict[str, str] = {}
        self.converted_unsafe_reasons: dict[str, UnsafeReason] = {}
        convertible: dict[str, tuple[tuple[str, bool], list[PythonCstNode]]] = {}
        generic_classes_by_name: dict[str, list[PythonCstNode]] = {}
        blocked: set[int] = set()
        for name, decl_stmt in find_type_param_declarations(module).items():
            self.type_param_kinds[name] = type_param_constructor_name(decl_stmt)
            uses = uses_of(root, name, decl_stmt)
            signature_users = {id(function) for use in uses if (function := signature_function(use)) is not None}
            functions = list(dict.fromkeys(function for use in uses if (function := owning_function(use, signature_users)) is not None))
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
                blocked.update(id(function) for function in candidates)
                continue

            convertible[name] = ((type_param_text(decl_stmt, module), declared_default(decl_stmt) is not None), candidates)
            generic_classes_by_name[name] = classes

        # One self.replace() per function: a function using two converted names would otherwise get two
        # rewrites of the same node, which the rewriter rejects as conflicting.
        new_params: dict[int, tuple[PythonCstNode, list[tuple[str, bool]]]] = {}
        for name, (param, candidates) in convertible.items():
            allowed = [function for function in candidates if id(function) not in blocked]
            if not allowed:
                self._mark_unsafe(results, self.converted_unsafe_reasons, name, UnsafeReason.SHARES_FUNCTION_WITH_UNCONVERTIBLE)
                continue
            for function in allowed:
                new_params.setdefault(id(function), (function, []))[1].append(param)
            results[name] = "fixed"

        for function, params in new_params.values():
            self._add_type_params(function, params)

        self._report_generic_class_leftovers(results, generic_classes_by_name)
        return results

    def _report_generic_class_leftovers(self, results: dict[str, str], generic_classes_by_name: dict[str, list[PythonCstNode]]) -> None:
        """Add USED_IN_GENERIC_CLASS to converted_unsafe_reasons for each "fixed" name a generic class still uses."""
        for name, classes in generic_classes_by_name.items():
            if classes and results.get(name) == "fixed":
                self.converted_unsafe_reasons[name] = UnsafeReason.USED_IN_GENERIC_CLASS

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
        with its UnsafeReason on self.orphaned_unsafe_reasons. Records each declaration's kind on
        self.type_param_kinds. Returns {name: "fixed" | "unsafe"}.
        """
        root = self._cst_root()
        module = root.translation_unit.atu

        results: dict[str, str] = {}
        self.orphaned_unsafe_reasons: dict[str, UnsafeReason] = {}
        for name, decl_stmt in find_type_param_declarations(module).items():
            self.type_param_kinds[name] = type_param_constructor_name(decl_stmt)
            if uses_of(root, name, decl_stmt):
                continue

            reason = is_safe_to_remove(module, name, self.project_wide_imported_names)
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

    def _remove_declaration(self, decl_stmt: cst.Assign) -> None:
        """Remove decl_stmt's statement from the file, with the comment trailing it when it is alone on its line."""
        unit = self._cst_root().translation_unit
        targets: list[cst.CSTNode] = [decl_stmt]
        trailing = trailing_of_sole_statement(unit.atu, decl_stmt)
        if trailing is not None and trailing.comment is not None:
            targets.append(trailing.comment)
        # TODO(FrancescoPezzella): enable once comment blocks get correctly deleted
        #  https://github.com/TNO/Renaissance.Py/issues/189
        self.remove([unit.wrappers[target] for target in targets], include_comments=False)

    def localize_imported_typevars(self) -> dict[str, str]:
        """Replace imports of TypeVar/ParamSpec/TypeVarTuple names from the target project with local declarations.

        Imports are resolved against project_root. Where safe, the import is dropped and a copy of the origin's
        declaration is added, plus imports for the names its arguments use (e.g. `bound=Shape`), from the module
        the origin gets each one from. The added imports (each once per file) and declarations go after the
        file's last import, so no import is left below code. A declaration stays where its import was when a
        statement in between uses it.
        It is unsafe when is_safe_to_localize rejects the origin or _argument_imports returns None.
        Returns {name: "fixed" | "unsafe"}, with each UnsafeReason on self.cross_file_unsafe_reasons.
        """
        results: dict[str, str] = {}
        self.cross_file_unsafe_reasons: dict[str, UnsafeReason] = {}
        module = self._cst_root().translation_unit.atu

        project_root = self.project_root if self.project_root is not None else Path(self.filename).parent
        localizations: list[_Localization] = []
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
                self._localize_names_from(line, statement, origin_path, results, localizations)

        self._place_localizations(localizations)
        return results

    def _localize_names_from(
        self,
        line: cst.SimpleStatementLine,
        raw: cst.ImportFrom,
        origin_path: Path,
        results: dict[str, str],
        localizations: list[_Localization],
    ) -> None:
        """Queue the localization of every safe type parameter name that raw, on line, imports from the origin_path file.

        Records each name in results as "fixed" or, via _mark_unsafe, as "unsafe", its kind on
        self.type_param_kinds, and appends what to write for the "fixed" ones to localizations.

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

        for alias in raw.names:
            name = alias.evaluated_name
            if alias.asname is not None or name not in declarations:
                continue

            decl_stmt = declarations[name]
            self.type_param_kinds[name] = type_param_constructor_name(decl_stmt)
            reason = is_safe_to_localize(origin, name)
            if reason is not None:
                self._mark_unsafe(results, self.cross_file_unsafe_reasons, name, reason)
                continue
            argument_imports = self._argument_imports(origin, origin_path, raw, decl_stmt)
            if argument_imports is None:
                self._mark_unsafe(results, self.cross_file_unsafe_reasons, name, UnsafeReason.DECLARATION_NAME_UNAVAILABLE)
                continue

            constructor_import = self._missing_constructor_import(origin, origin_path, raw, decl_stmt)
            for needed in [constructor_import, *argument_imports]:
                if needed is not None and needed not in needed_imports:
                    needed_imports.append(needed)
            localized[name] = decl_stmt
            results[name] = "fixed"

        if not localized:
            return
        localizations.append(self._localization(line, raw, origin, localized, needed_imports))

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

    def _argument_imports(
        self,
        origin: cst.Module,
        origin_path: Path,
        raw: cst.ImportFrom,
        decl_stmt: cst.Assign,
    ) -> list[str] | None:
        """Return the import lines for the names decl_stmt's arguments use that this file doesn't have, sorted by name.

        A name this file already imports from the origin module (or from the same absolute module the
        origin imports it from) is fine and not returned. Returns None if one of the names can't be
        imported as the same object: the origin doesn't bind it at module level at runtime (e.g. only
        under `if TYPE_CHECKING:`), or this file binds it to something else.
        """
        origin_sources = from_import_sources(origin)
        importing_sources = from_import_sources(self._cst_root().translation_unit.atu)
        imports: list[str] = []
        for name in sorted(declaration_argument_names(decl_stmt)):
            if name not in origin_sources:
                return None
            if name not in importing_sources:
                imports.append(self._argument_import(origin, origin_path, raw, name))
                continue
            origin_source = origin_sources[name]
            accepted = {(import_from_module(raw) or "", len(raw.relative))}
            if origin_source is not None and origin_source[1] == 0:
                accepted.add(origin_source)
            if importing_sources[name] not in accepted:
                return None
        return imports

    def _argument_import(self, origin: cst.Module, origin_path: Path, via: cst.ImportFrom, name: str) -> str:
        """Return the import line for name, which a localized declaration uses and the origin binds at module level.

        A name the origin imports is imported from the module it gets it from, as named from this file, which
        reaches the origin (origin_path) through via. Any other name, or one this file can't name the module
        of, is imported from the origin module itself.
        """
        binding = from_import_binding(origin, name)
        if binding is not None:
            statement, alias = binding
            module = rebase_relative_module(
                import_from_module(via),
                len(via.relative),
                origin_path,
                import_from_module(statement) or None,
                len(statement.relative),
            )
            if module is not None:
                imported = alias.evaluated_name
                return f"from {module} import {name if imported == name else f'{imported} as {name}'}"
        return f"from {self._import_from_text(via)} import {name}"

    @staticmethod
    def _localization(
        line: cst.SimpleStatementLine,
        raw: cst.ImportFrom,
        origin: cst.Module,
        declarations: dict[str, cst.Assign],
        needed_imports: list[str],
    ) -> _Localization:
        """Return what replaces the names of declarations that the import raw, on line, brings in.

        The declarations keep their original formatting and the comment trailing them. needed_imports are the
        imports they need (their constructors, names their arguments use) that this file doesn't have yet. The
        kept aliases are the names raw imports that are not localized.
        """
        kept = [alias for alias in cast("Sequence[cst.ImportAlias]", raw.names) if imported_name(alias) not in declarations]
        if kept and raw.rpar is None:
            # Without parentheses, a trailing comma after the last name is a syntax error.
            kept[-1] = kept[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        # TODO(FrancescoPezzella): the comment lines above a declaration are not copied: the rewriter only handles a one-line comment.
        #  https://github.com/TNO/Renaissance.Py/issues/189
        texts = [declaration_text(origin, decl) for decl in declarations.values()]
        return _Localization(line, raw, frozenset(declarations), kept, needed_imports, texts)

    @staticmethod
    def _is_import_line(statement: cst.BaseStatement) -> bool:
        """Return True if statement is a line made only of import statements."""
        return isinstance(statement, cst.SimpleStatementLine) and all(
            isinstance(small, cst.Import | cst.ImportFrom) for small in statement.body
        )

    def _place_localizations(self, localizations: list[_Localization]) -> None:
        """Write each localization: its import is narrowed or dropped, and what replaces its names goes after the last import.

        The needed imports come first, each once, then the declarations. If every import of the file is dropped, they
        take the place of the last one. A localization is written where its import is when that import shares its
        line with other statements and would be dropped, when no import remains to go after, or when a statement
        between it and the last import reads one of its names.
        """
        body = self._cst_root().translation_unit.atu.body
        wrappers = self._cst_root().translation_unit.wrappers
        dropped = {id(item.line) for item in localizations if not item.kept}
        anchor = max(
            (index for index, statement in enumerate(body) if self._is_import_line(statement) and id(statement) not in dropped),
            default=None,
        )
        replaces_anchor = anchor is None
        if anchor is None:
            anchor = max(
                (
                    index
                    for index, statement in enumerate(body)
                    if id(statement) in dropped and isinstance(statement, cst.SimpleStatementLine) and len(statement.body) == 1
                ),
                default=None,
            )
        if anchor is None:
            for item in localizations:
                self._write_in_place(item)
            return

        imports: list[str] = []
        declarations: list[str] = []
        anchor_raw: cst.ImportFrom | None = None
        for item in localizations:
            if not self._goes_after_last_import(item, body, anchor):
                self._write_in_place(item)
                continue
            imports.extend(item.imports)
            declarations.extend(item.declarations)
            if replaces_anchor and item.line is body[anchor]:
                anchor_raw = item.raw
            elif item.kept:
                self._narrow(item)
            else:
                self._drop(item)

        if not declarations:
            return
        text = "\n".join([*dict.fromkeys(imports), *declarations])
        if anchor_raw is not None:
            self.replace(text, wrappers[anchor_raw], include_whitespace=False, include_comments=False)
        else:
            self.insert_after(f"\n{text}", wrappers[body[anchor]], include_whitespace=False, include_comments=True)

    def _write_in_place(self, item: _Localization) -> None:
        """Replace the names of item where its import is: its needed imports and declarations follow the kept names, if any."""
        wrappers = self._cst_root().translation_unit.wrappers
        text = "\n".join([*item.imports, *item.declarations])
        if not item.kept:
            self.replace(text, wrappers[item.raw], include_whitespace=False, include_comments=False)
            return
        self._narrow(item)
        self.insert_after(f"\n{text}", wrappers[item.line], include_whitespace=False, include_comments=True)

    def _drop(self, item: _Localization) -> None:
        """Remove the import of item, with the comment trailing it, from its line."""
        wrappers = self._cst_root().translation_unit.wrappers
        targets = [wrappers[item.raw]]
        comment = item.line.trailing_whitespace.comment
        if comment is not None:
            targets.append(wrappers[comment])
        self.remove(targets, include_comments=False)

    def _narrow(self, item: _Localization) -> None:
        """Replace the import of item with one that only imports its kept names, keeping its comments."""
        module = self._cst_root().translation_unit.atu
        narrowed = module.code_for_node(item.raw.with_changes(names=item.kept, semicolon=cst.MaybeSentinel.DEFAULT))
        self.replace(narrowed, self._cst_root().translation_unit.wrappers[item.raw], include_whitespace=False, include_comments=False)

    def _goes_after_last_import(self, item: _Localization, body: Sequence[cst.BaseStatement], anchor: int) -> bool:
        """Return True if item can be written after body[anchor], the last import that stays.

        It can't when its import would be dropped from a line with other statements, or when a statement
        between it and the anchor that isn't an import reads one of its names: moving the declaration
        down would define it after that use.
        """
        if not item.kept and len(item.line.body) != 1:
            return False
        index = next(position for position, statement in enumerate(body) if statement is item.line)
        return not any(
            not self._is_import_line(statement) and item.names & names_read_by(statement) for statement in body[index + 1 : anchor]
        )

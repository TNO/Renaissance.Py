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
from renaissance.recipes.type_parameter_declarations import (
    declared_default,
    find_type_param_declarations,
    generic_classes,
    has_unconvertible_argument,
    import_from_module,
    imported_name,
    is_safe_to_localize,
    is_safe_to_remove,
    owning_function,
    signature_function,
    trailing_of_sole_statement,
    type_param_constructor_name,
    type_param_text,
    type_params_bracket,
)
from renaissance.recipes.type_parameter_localization import Localization, plan_localizations
from renaissance.recipes.type_parameter_rules import (
    UnsafeReason,
    conversion_refusal,
    is_safe_to_remove,
    mark_unsafe,
)
from renaissance.recipes.type_parameter_uses import (
    generic_classes,
    owning_function,
    signature_function,
    uses_of,
)
from renaissance.utils.cst_utils import names_read_by, trailing_of_sole_statement
from renaissance.utils.import_resolution import is_import_line

MIN_SUPPORTED_PYTHON = (3, 12)


class TypeParameterCheck(PythonRefactoring[PythonCstNode]):
    """Modernize legacy TypeVar/ParamSpec/TypeVarTuple usage in a Python file to PEP 695 syntax.

    Attributes:
        min_python: Minimum Python version the target codebase supports (default 3.12, where PEP 695 syntax exists).
        project_wide_imported_names: Names other project files import from this file; never removed.
        project_root: Root that absolute imports resolve from; the file's own directory if None.
        ignore_localize_origins: Absolute paths of files whose declarations are never copied into their importers.
        localize_imports: When False, no declaration is copied into the files importing it.
        type_param_kinds: Each declared name the phases see, mapped to "TypeVar", "ParamSpec" or "TypeVarTuple".
        ignored_names: Type parameter names this file imports from an ignored origin, or from any project file when
            localize_imports is False; they keep their import.
        cross_file_unsafe_reasons: Why each "unsafe" name of the first phase was refused.
        converted_unsafe_reasons: The same for the second phase; also holds "fixed" names a generic class still uses.
        orphaned_unsafe_reasons: The same for the third phase.

    """

    min_python: tuple[int, int] = MIN_SUPPORTED_PYTHON
    project_wide_imported_names: frozenset[str] = frozenset()
    project_root: Path | None = None
    ignore_localize_origins: frozenset[Path] = frozenset()
    localize_imports: bool = True

    def __init__(self, file: Path) -> None:
        """Prepare the recipe for file, parsed with the CST backend."""
        super().__init__(file, PythonCstNode)
        self.type_param_kinds: dict[str, str] = {}
        self.ignored_names: set[str] = set()

    def run(self) -> None:
        """Run check() and store its result on self.result."""
        self.result = self.check()

    def _cst_root(self) -> PythonCstNode:
        """Return the root node of the file as it currently is (after the last commit)."""
        return cast("PythonCstNode", cast("object", self.root))

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
        """Add PEP 695 type parameters to the functions whose signatures use a module-level TypeVar/ParamSpec/TypeVarTuple.

        The declaration stays. Methods of a class generic over the name are left unchanged, and so is a function that
        also uses a declaration conversion_refusal rejects, so no function mixes legacy and PEP 695 type parameters.
        Bounds, constraints and `default=` are carried over, defaulted ones last. Returns {name: "fixed" | "unsafe"},
        with each UnsafeReason on self.converted_unsafe_reasons; a "fixed" name that a generic class still uses gets
        USED_IN_GENERIC_CLASS there too.
        """
        root = self._cst_root()
        module = root.translation_unit.atu

        results: dict[str, str] = {}
        self.converted_unsafe_reasons: dict[str, UnsafeReason] = {}
        convertible, generic_classes_by_name, blocked = self._plan_conversions(root, module, results)

        # One self.replace() per function: a function using two converted names would otherwise get two
        # rewrites of the same node, which the rewriter rejects as conflicting.
        new_params: dict[int, tuple[PythonCstNode, list[tuple[str, bool]]]] = {}
        for name, (param, candidates) in convertible.items():
            allowed = [function for function in candidates if id(function) not in blocked]
            if not allowed:
                mark_unsafe(results, self.converted_unsafe_reasons, name, UnsafeReason.SHARES_FUNCTION_WITH_UNCONVERTIBLE)
                continue
            for function in allowed:
                new_params.setdefault(id(function), (function, []))[1].append(param)
            results[name] = "fixed"

        for function, params in new_params.values():
            self._add_type_params(function, params)

        self._report_generic_class_leftovers(results, generic_classes_by_name)
        return results

    def _plan_conversions(
        self, root: PythonCstNode, module: cst.Module, results: dict[str, str]
    ) -> tuple[dict[str, tuple[tuple[str, bool], list[PythonCstNode]]], dict[str, list[PythonCstNode]], set[int]]:
        """Return what each declaration that can be converted needs, marking in results the ones that can't.

        Returns {name: ((type parameter text, has default), functions to convert)}, {name: classes generic over it}
        and the ids of the functions a refused declaration also uses, which must stay unchanged.
        """
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
            # TODO(FrancescoPezzella): convert a class with the name in a base (`class Box(Base[T])`) to
            #  `class Box[T](Base[T])`, still refusing `covariant=`.
            #  https://github.com/TNO/Renaissance.Py/issues/279
            # Maybe ruff's UP046 could take over one day, if it handles bases other than `Generic`:
            # https://github.com/astral-sh/ruff/issues/29481
            in_generic_class = [function for function in functions if self._is_inside(function, classes)]
            candidates = [function for function in functions if function not in in_generic_class]
            if not candidates:
                if in_generic_class:
                    mark_unsafe(results, self.converted_unsafe_reasons, name, UnsafeReason.USED_IN_GENERIC_CLASS)
                continue
            reason = conversion_refusal(decl_stmt, self.min_python)
            if reason is not None:
                mark_unsafe(results, self.converted_unsafe_reasons, name, reason)
                blocked.update(id(function) for function in candidates)
                continue

            convertible[name] = ((type_param_text(decl_stmt, module), declared_default(decl_stmt) is not None), candidates)
            generic_classes_by_name[name] = classes
        return convertible, generic_classes_by_name, blocked

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
        """Add params, given as (text, has_default), to function's PEP 695 type parameters.

        A function without a bracket gets one after its name; an existing bracket is rebuilt with params after its own,
        defaulted ones last, which drops its comments and line breaks.
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
        """Remove every module-level TypeVar/ParamSpec/TypeVarTuple declaration that nothing uses.

        A declaration that is_safe_to_remove rejects is kept and reported "unsafe", with its UnsafeReason on
        self.orphaned_unsafe_reasons. Returns {name: "fixed" | "unsafe"}.
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
                mark_unsafe(results, self.orphaned_unsafe_reasons, name, reason)
                continue

            self._remove_declaration(decl_stmt)
            results[name] = "fixed"

        return results

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
        declaration, plus the imports it needs, is added after the file's last import. Names from an
        ignore_localize_origins file, or all names when localize_imports is False, keep their import and go to
        self.ignored_names. Returns {name: "fixed" | "unsafe"}, with each UnsafeReason on
        self.cross_file_unsafe_reasons.

        Raises:
            SyntaxError: if an origin file can't be parsed.

        """
        project_root = self.project_root if self.project_root is not None else Path(self.filename).parent
        plan = plan_localizations(
            self._cst_root().translation_unit.atu,
            Path(self.filename),
            project_root,
            localize_imports=self.localize_imports,
            ignore_origins=self.ignore_localize_origins,
        )
        self.cross_file_unsafe_reasons: dict[str, UnsafeReason] = plan.unsafe_reasons
        self.type_param_kinds.update(plan.kinds)
        self.ignored_names |= plan.ignored_names
        self._place_localizations(plan.localizations)
        return plan.results

    def _place_localizations(self, localizations: list[Localization]) -> None:
        """Write the localizations: narrow or drop each import, then add the needed imports and declarations after the last one.

        Each needed import is added once, before the declarations; if every import is dropped, they take the place of the
        last one. A localization is written in place of its import instead when that import shares a line with other
        statements and would be dropped, when no import remains to go after, or when a statement in between reads one
        of its names.
        """
        body = self._cst_root().translation_unit.atu.body
        wrappers = self._cst_root().translation_unit.wrappers
        dropped = {id(item.line) for item in localizations if not item.kept}
        anchor, replaces_anchor = self._anchor_index(body, dropped)
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

    def _anchor_index(self, body: Sequence[cst.BaseStatement], dropped: set[int]) -> tuple[int | None, bool]:
        """Return the index in body of the statement that localized text goes after, and whether it replaces that statement.

        The anchor is the last import line that stays. If every import is dropped, it is the last dropped line holding
        a single statement, whose place the text takes. The index is None when body has neither.
        """
        anchor = max(
            (index for index, statement in enumerate(body) if is_import_line(statement) and id(statement) not in dropped),
            default=None,
        )
        if anchor is not None:
            return anchor, False
        anchor = max(
            (
                index
                for index, statement in enumerate(body)
                if id(statement) in dropped and isinstance(statement, cst.SimpleStatementLine) and len(statement.body) == 1
            ),
            default=None,
        )
        return anchor, True

    def _write_in_place(self, item: Localization) -> None:
        """Replace the names of item where its import is: its needed imports and declarations follow the kept names, if any."""
        wrappers = self._cst_root().translation_unit.wrappers
        text = "\n".join([*item.imports, *item.declarations])
        if not item.kept:
            self.replace(text, wrappers[item.raw], include_whitespace=False, include_comments=False)
            return
        self._narrow(item)
        self.insert_after(f"\n{text}", wrappers[item.line], include_whitespace=False, include_comments=True)

    def _drop(self, item: Localization) -> None:
        """Remove the import of item, with the comment trailing it, from its line."""
        wrappers = self._cst_root().translation_unit.wrappers
        targets = [wrappers[item.raw]]
        comment = item.line.trailing_whitespace.comment
        if comment is not None:
            targets.append(wrappers[comment])
        self.remove(targets, include_comments=False)

    def _narrow(self, item: Localization) -> None:
        """Replace the import of item with one that only imports its kept names, keeping its comments."""
        module = self._cst_root().translation_unit.atu
        narrowed = module.code_for_node(item.raw.with_changes(names=item.kept, semicolon=cst.MaybeSentinel.DEFAULT))
        self.replace(narrowed, self._cst_root().translation_unit.wrappers[item.raw], include_whitespace=False, include_comments=False)

    def _goes_after_last_import(self, item: Localization, body: Sequence[cst.BaseStatement], anchor: int) -> bool:
        """Return True if item can be written after body[anchor], the last import that stays.

        It can't if its import would be dropped from a line with other statements, or if a non-import statement between
        that import and the anchor reads one of its names.
        """
        if not item.kept and len(item.line.body) != 1:
            return False
        index = next(position for position, statement in enumerate(body) if statement is item.line)
        return not any(not is_import_line(statement) and item.names & names_read_by(statement) for statement in body[index + 1 : anchor])

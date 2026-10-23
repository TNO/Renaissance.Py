# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Decide which TypeVar/ParamSpec/TypeVarTuple names a file imports from its project get a local declaration instead."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import libcst as cst

from renaissance.recipes.type_parameter_declarations import (
    declaration_argument_names,
    declaration_text,
    find_type_param_declarations,
    type_param_constructor_name,
)
from renaissance.recipes.type_parameter_rules import UnsafeReason, is_safe_to_localize, mark_unsafe
from renaissance.utils.cst_utils import module_statements
from renaissance.utils.import_resolution import (
    from_import_binding,
    from_import_sources,
    import_from_module,
    import_from_text,
    imported_name,
    rebase_relative_module,
    resolve_project_module,
)


@dataclass(frozen=True)
class Localization:
    """The type parameter names one import statement brings in that are localized, and the text that replaces them."""

    line: cst.SimpleStatementLine
    raw: cst.ImportFrom
    names: frozenset[str]
    kept: list[cst.ImportAlias]
    imports: list[str]
    declarations: list[str]


@dataclass
class LocalizationPlan:
    """What plan_localizations decides for one file.

    Attributes:
        localizations: What to write for each import that has names to localize.
        results: Each name seen, mapped to "fixed" or "unsafe".
        unsafe_reasons: Why each "unsafe" name was refused.
        kinds: Each name seen, mapped to "TypeVar", "ParamSpec" or "TypeVarTuple".
        ignored_names: The names kept as imports because their origin is ignored or localization is off.

    """

    localizations: list[Localization] = field(default_factory=list[Localization])
    results: dict[str, str] = field(default_factory=dict[str, str])
    unsafe_reasons: dict[str, UnsafeReason] = field(default_factory=dict[str, UnsafeReason])
    kinds: dict[str, str] = field(default_factory=dict[str, str])
    ignored_names: set[str] = field(default_factory=set[str])


def plan_localizations(
    module: cst.Module,
    filename: Path,
    project_root: Path,
    *,
    localize_imports: bool,
    ignore_origins: frozenset[Path],
) -> LocalizationPlan:
    """Decide, for every `from X import ...` of module that resolves to a project file, which type parameters to localize.

    Imports are resolved against project_root. Names from a file in ignore_origins, or all names when localize_imports
    is False, are kept as imports and go to the plan's ignored_names.

    Raises:
        SyntaxError: if an origin file can't be parsed, with its path as the filename.

    """
    return _Planner(module, filename, project_root, localize_imports, ignore_origins).run()


@dataclass(frozen=True)
class _Planner:
    """Decide the localizations of one file, whose parsed module is `module` and path is `filename`."""

    module: cst.Module
    filename: Path
    project_root: Path
    localize_imports: bool
    ignore_origins: frozenset[Path]

    def run(self) -> LocalizationPlan:
        """Return the plan for every project import of the module."""
        plan = LocalizationPlan()
        for line in self.module.body:
            if not isinstance(line, cst.SimpleStatementLine):
                continue
            for statement in line.body:
                if not isinstance(statement, cst.ImportFrom):
                    continue
                origin_path = resolve_project_module(
                    self.filename, self.project_root, import_from_module(statement), len(statement.relative)
                )
                if origin_path is None:
                    continue
                self._localize_names_from(plan, line, statement, origin_path)
        return plan

    def _localize_names_from(self, plan: LocalizationPlan, line: cst.SimpleStatementLine, raw: cst.ImportFrom, origin_path: Path) -> None:
        """Queue the localization of every safe type parameter name that raw, on line, imports from the origin_path file.

        Records each name in the plan's results as "fixed" or, via mark_unsafe, as "unsafe", its kind in kinds, and
        appends what to write for the "fixed" ones to localizations.
        """
        if isinstance(raw.names, cst.ImportStar):
            return
        origin = _parse_origin(origin_path)
        declarations = find_type_param_declarations(origin)
        localized: dict[str, cst.Assign] = {}
        needed_imports: list[str] = []

        for alias in raw.names:
            name = alias.evaluated_name
            if alias.asname is not None or name not in declarations:
                continue

            decl_stmt = declarations[name]
            plan.kinds[name] = type_param_constructor_name(decl_stmt)
            if not self.localize_imports or origin_path in self.ignore_origins:
                plan.ignored_names.add(name)
                continue
            reason = is_safe_to_localize(origin, name)
            if reason is not None:
                mark_unsafe(plan.results, plan.unsafe_reasons, name, reason)
                continue
            argument_imports = self._argument_imports(origin, origin_path, raw, decl_stmt)
            if argument_imports is None:
                mark_unsafe(plan.results, plan.unsafe_reasons, name, UnsafeReason.NAME_NOT_AT_MODULE_LEVEL)
                continue

            constructor_import = self._missing_constructor_import(origin, origin_path, raw, decl_stmt)
            for needed in [constructor_import, *argument_imports]:
                if needed is not None and needed not in needed_imports:
                    needed_imports.append(needed)
            localized[name] = decl_stmt
            plan.results[name] = "fixed"

        if not localized:
            return
        plan.localizations.append(_localization(line, raw, origin, localized, needed_imports))

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
        ctor_module = ctor_module or import_from_text(via)

        # TODO(FrancescoPezzella): the constructor already imported here from another module (e.g. `typing` vs the origin's
        #  `typing_extensions`) isn't matched, so a second, shadowing import of the same name is added.
        #  https://github.com/TNO/Renaissance.Py/issues/279
        for statement in module_statements(self.module):
            if (
                isinstance(statement, cst.ImportFrom)
                and not isinstance(statement.names, cst.ImportStar)
                and import_from_text(statement) == ctor_module
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
        origin imports it from) is fine and not returned. Returns None if one of the names isn't available
        as the same object at module level: the origin doesn't bind it at runtime (e.g. only under
        `if TYPE_CHECKING:`), or this file binds it to something else.
        """
        origin_sources = from_import_sources(origin)
        importing_sources = from_import_sources(self.module)
        imports: list[str] = []
        for name in sorted(declaration_argument_names(decl_stmt)):
            if name not in origin_sources:
                return None
            if name not in importing_sources:
                imports.append(_argument_import(origin, origin_path, raw, name))
                continue
            origin_source = origin_sources[name]
            accepted = {(import_from_module(raw) or "", len(raw.relative))}
            if origin_source is not None and origin_source[1] == 0:
                accepted.add(origin_source)
            if importing_sources[name] not in accepted:
                return None
        return imports


def _parse_origin(origin_path: Path) -> cst.Module:
    """Return the parsed origin_path file.

    Raises:
        SyntaxError: if the file can't be parsed, with origin_path as its filename.

    """
    try:
        return cst.parse_module(origin_path.read_text(encoding="utf-8"))
    except cst.ParserSyntaxError as error:
        raise SyntaxError(error.message, (str(origin_path), error.raw_line, error.raw_column + 1, None)) from error


def _argument_import(origin: cst.Module, origin_path: Path, via: cst.ImportFrom, name: str) -> str:
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
    return f"from {import_from_text(via)} import {name}"


def _localization(
    line: cst.SimpleStatementLine,
    raw: cst.ImportFrom,
    origin: cst.Module,
    declarations: dict[str, cst.Assign],
    needed_imports: list[str],
) -> Localization:
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
    return Localization(line, raw, frozenset(declarations), kept, needed_imports, texts)

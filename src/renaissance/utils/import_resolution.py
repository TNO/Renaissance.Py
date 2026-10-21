# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Read the import statements of a module, and resolve project-internal `from X import Y` to the .py file they import from."""

from collections.abc import Sequence
from pathlib import Path
from typing import cast

import libcst as cst
from libcst import matchers
from libcst.helpers import get_full_name_for_node

from renaissance.utils.cst_utils import assigned_names, module_statements


def import_from_module(statement: cst.ImportFrom) -> str | None:
    """Return the dotted module an import-from names after its leading dots, or None for a bare `from . import x`."""
    return get_full_name_for_node(statement.module) if statement.module is not None else None


def imported_name(alias: cst.ImportAlias) -> str:
    """Return the name an import alias binds: its `as` name if it has one, else the imported name."""
    return alias.evaluated_alias or alias.evaluated_name


def import_from_text(statement: cst.ImportFrom) -> str:
    """Return what follows `from` in an import-from: its leading dots and dotted module, e.g. "..pkg.mod"."""
    return "." * len(statement.relative) + (import_from_module(statement) or "")


def is_import_line(statement: cst.BaseStatement) -> bool:
    """Return True if statement is a line made only of import statements."""
    return isinstance(statement, cst.SimpleStatementLine) and all(
        isinstance(small, cst.Import | cst.ImportFrom) for small in statement.body
    )


def from_import_sources(module: cst.Module) -> dict[str, tuple[str, int] | None]:
    """Map every name bound at module level to its `from` import's (module, level), or None if bound otherwise.

    Names bound by a class, function, assignment or plain `import` map to None.
    """
    sources: dict[str, tuple[str, int] | None] = {}
    for statement in module_statements(module):
        if isinstance(statement, cst.ImportFrom):
            source = (import_from_module(statement) or "", len(statement.relative))
            if isinstance(statement.names, cst.ImportStar):
                sources["*"] = source
            else:
                for alias in statement.names:
                    sources[imported_name(alias)] = source
        elif isinstance(statement, cst.Import):
            for alias in statement.names:
                sources[imported_name(alias).split(".")[0]] = None
        elif isinstance(statement, cst.ClassDef | cst.FunctionDef):
            sources[statement.name.value] = None
        elif isinstance(statement, cst.Assign | cst.AnnAssign):
            sources.update(dict.fromkeys(assigned_names(statement)))
    return sources


def from_import_binding(module: cst.Module, name: str) -> tuple[cst.ImportFrom, cst.ImportAlias] | None:
    """Return the module-level `from` import and the alias that bind name, or None if another statement binds it last."""
    if from_import_sources(module).get(name) is None:
        return None
    binding: tuple[cst.ImportFrom, cst.ImportAlias] | None = None
    for statement in module_statements(module):
        if isinstance(statement, cst.ImportFrom) and not isinstance(statement.names, cst.ImportStar):
            binding = next(((statement, alias) for alias in statement.names if imported_name(alias) == name), binding)
    return binding


def imports_name_conditionally(module: cst.Module, name: str) -> bool:
    """Return True if an import inside a module-level `if`/`try` block binds `name`."""
    for statement in module.body:
        if not isinstance(statement, cst.If | cst.Try | cst.TryStar):
            continue
        for node in matchers.findall(statement, matchers.Import() | matchers.ImportFrom()):
            names = cast("cst.Import | cst.ImportFrom", node).names
            if not isinstance(names, cst.ImportStar) and any(imported_name(alias).split(".")[0] == name for alias in names):
                return True
    return False


def resolve_project_module(importing_file: Path, project_root: Path, module: str | None, level: int) -> Path | None:
    """Resolve one import-from's `(module, level)` to a concrete .py file under `project_root`.

    `level == 0` is an absolute import (`module` is dotted from `project_root`, e.g.
    "redis.typing"). `level >= 1` is relative (PEP 328): anchor at `importing_file`'s own
    directory for level 1, walking up `level - 1` further parent directories for each extra dot
    (`from ..module import x`); `module` is None for a bare `from . import x`, which resolves to
    the anchor directory's own `__init__.py`.

    Tries `<path>.py` first, then `<path>/__init__.py`. Returns None if neither exists or if
    resolution would walk above `project_root`, as for a stdlib or third-party import. The returned
    path is always absolute.
    """
    # A relative path can't walk above itself: Path("a.py").parent.parent is still Path(".").
    importing_file = importing_file.absolute()
    project_root = project_root.absolute()
    if level == 0:
        anchor = project_root
    else:
        anchor = importing_file.parent
        for _ in range(level - 1):
            anchor = anchor.parent
        if project_root not in (anchor, *anchor.parents):
            return None

    candidate = anchor / (module.replace(".", "/") + ".py") if module is not None else anchor / "__init__.py"
    if candidate.is_file():
        return candidate
    if module is not None:
        candidate_package = anchor / module.replace(".", "/") / "__init__.py"
        if candidate_package.is_file():
            return candidate_package
    return None


def rebase_relative_module(via_module: str | None, via_level: int, origin_file: Path, module: str | None, level: int) -> str | None:
    """Rewrite an import target of the origin module so that the importing file names the same module.

    The importing file reaches the origin (`origin_file`) with `from <via> import ...`, where `via` is
    `via_level` dots followed by `via_module`. The origin's own `from <module> import ...` with `level`
    dots is re-anchored on that same path, e.g. via ".sub.file_1" and "._compat" give ".sub._compat".
    An absolute import (`level == 0`) is returned unchanged.

    Returns the text that follows `from`, or None if the importing file can't name the module: an
    absolute `via` to a top-level origin leaves no package for the relative import to start from.
    """
    if level == 0:
        return module
    parts = via_module.split(".") if via_module is not None else []
    if origin_file.name != "__init__.py":
        parts = parts[:-1]
    dots = via_level
    for _ in range(level - 1):
        if parts:
            parts.pop()
        elif dots > 0:
            dots += 1
        else:
            return None
    if dots == 0 and not parts:
        return None
    if module is not None:
        parts.append(module)
    return "." * dots + ".".join(parts)


def collect_project_imported_names(files: Sequence[Path], project_root: Path) -> dict[Path, frozenset[str]]:
    """Map each project file to the names any file in `files` imports or reads from it.

    Two kinds of dependency are recorded against the resolved origin file:

    - `from module import name`: `alias.name` (the name as declared in the origin module, not
      `alias.asname`) - an aliased import still depends on the original name existing.
    - An attribute read through an imported project module (`import pkg.mod` then `pkg.mod.T`,
      `import pkg.mod as m` then `m.T`, `from pkg import mod` then `mod.T`): the attribute name.

    Imports that don't resolve inside `project_root` (stdlib/third-party) are skipped, as is any
    file that can't be read or parsed.
    """
    imported: dict[Path, set[str]] = {}
    for file in files:
        try:
            module = cst.parse_module(file.read_text(encoding="utf-8"))
        except OSError, cst.ParserSyntaxError:
            continue
        module_bindings: dict[str, Path] = {}
        for statement in matchers.findall(module, matchers.ImportFrom() | matchers.Import()):
            if isinstance(statement, cst.ImportFrom):
                _record_from_import(file, project_root, statement, imported, module_bindings)
            else:
                _bind_imported_modules(file, project_root, cast("cst.Import", statement), module_bindings)
        _record_module_attribute_reads(module, module_bindings, imported)
    return {path: frozenset(names) for path, names in imported.items()}


def _record_from_import(
    file: Path,
    project_root: Path,
    statement: cst.ImportFrom,
    imported: dict[Path, set[str]],
    module_bindings: dict[str, Path],
) -> None:
    """Record `statement`'s imported names against their origin, and bind any alias that is itself a project module."""
    module = import_from_module(statement)
    level = len(statement.relative)
    aliases = [] if isinstance(statement.names, cst.ImportStar) else list(statement.names)
    origin = resolve_project_module(file, project_root, module, level)
    if origin is not None:
        imported.setdefault(origin, set()).update([alias.evaluated_name for alias in aliases] or ["*"])
    for alias in aliases:
        submodule = f"{module}.{alias.evaluated_name}" if module is not None else alias.evaluated_name
        submodule_origin = resolve_project_module(file, project_root, submodule, level)
        if submodule_origin is not None:
            module_bindings[imported_name(alias)] = submodule_origin


def _bind_imported_modules(file: Path, project_root: Path, statement: cst.Import, module_bindings: dict[str, Path]) -> None:
    """Bind the dotted name(s) `statement` makes available to the project module file each one refers to."""
    for alias in statement.names:
        if alias.evaluated_alias is not None:
            origin = resolve_project_module(file, project_root, alias.evaluated_name, 0)
            if origin is not None:
                module_bindings[alias.evaluated_alias] = origin
            continue
        # `import a.b.c` binds `a`, and makes `a.b` and `a.b.c` reachable through it.
        parts = alias.evaluated_name.split(".")
        for end in range(1, len(parts) + 1):
            prefix = ".".join(parts[:end])
            origin = resolve_project_module(file, project_root, prefix, 0)
            if origin is not None:
                module_bindings[prefix] = origin


def _record_module_attribute_reads(module: cst.Module, module_bindings: dict[str, Path], imported: dict[Path, set[str]]) -> None:
    """Record every `<bound module>.<attr>` in `module` as a dependency on `attr` in that module's file."""
    if not module_bindings:
        return
    for node in matchers.findall(module, matchers.Attribute()):
        attribute = cast("cst.Attribute", node)
        dotted = _dotted_name(attribute.value)
        origin = module_bindings.get(dotted) if dotted is not None else None
        if origin is not None:
            imported.setdefault(origin, set()).add(attribute.attr.value)


def _dotted_name(expression: cst.BaseExpression) -> str | None:
    """Return `expression` as a dotted name (`a.b.c`) if it is a plain name/attribute chain, else None."""
    if isinstance(expression, cst.Name):
        return expression.value
    if isinstance(expression, cst.Attribute):
        base = _dotted_name(expression.value)
        return f"{base}.{expression.attr.value}" if base is not None else None
    return None

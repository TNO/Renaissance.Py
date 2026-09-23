"""Resolve project-internal `from X import Y` statements to the .py file they import from.

Used across an entire target codebase to check whether a declaration is still depended on by
another file before it's removed/rewritten - unlike `__all__`, an explicit `from module import
name` works regardless of whether the origin module declares `__all__`.
"""

import ast
from collections.abc import Sequence  # noqa: TC003 - no circular-import risk, not worth a TYPE_CHECKING block here
from pathlib import Path  # noqa: TC003 - same reason


def resolve_project_module(importing_file: Path, project_root: Path, module: str | None, level: int) -> Path | None:
    """Resolve one `ast.ImportFrom`'s `(module, level)` to a concrete .py file under `project_root`.

    `level == 0` is an absolute import (`module` is dotted from `project_root`, e.g.
    "redis.typing"). `level >= 1` is relative (PEP 328): anchor at `importing_file`'s own
    directory for level 1, walking up `level - 1` further parent directories for each extra dot
    (`from ..module import x`); `module` is None for a bare `from . import x`, which resolves to
    the anchor directory's own `__init__.py`.

    Tries `<path>.py` first, then `<path>/__init__.py` for a package-style import. Returns None
    if neither exists, or if resolution would walk above `project_root` - the common case for a
    stdlib/third-party import, which is exactly the signal used to exclude those as noise.
    Relative input paths are made absolute first, so the returned path is always absolute.

    # TODO: doesn't follow re-exports through an intermediate __init__.py, or handle namespace
    # packages (no __init__.py, PEP 420) - out of scope for now.
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


def collect_project_imported_names(files: Sequence[Path], project_root: Path) -> dict[Path, frozenset[str]]:
    """Map each project file to the names any file in `files` imports directly from it.

    Parses every file's `ImportFrom` statements, resolves each via `resolve_project_module`, and
    records `alias.name` (the name as declared in the origin module, not `alias.asname`) against
    the resolved origin file - an aliased import still depends on the original name existing.
    Imports that don't resolve inside `project_root` (stdlib/third-party) are skipped, as is any
    file that can't be read or parsed.
    """
    imported: dict[Path, set[str]] = {}
    for file in files:
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for stmt in ast.walk(tree):
            if not isinstance(stmt, ast.ImportFrom):
                continue
            origin = resolve_project_module(file, project_root, stmt.module, stmt.level)
            if origin is None:
                continue
            imported.setdefault(origin, set()).update(alias.name for alias in stmt.names)
    return {path: frozenset(names) for path, names in imported.items()}

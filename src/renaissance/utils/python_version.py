"""Detect the minimum Python version a target codebase declares support for, via the
nearest `pyproject.toml`'s `requires-python`. Shared by any recipe whose rewrite depends
on a minimum language version (e.g. PEP 695 syntax needs 3.12+).
"""

import tomllib
from pathlib import Path

from packaging.specifiers import InvalidSpecifier, SpecifierSet

KNOWN_PYTHON_VERSIONS = ("3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14")


def find_nearest_pyproject(start: Path) -> Path | None:
    """The nearest `pyproject.toml` at or above `start`, or None if none is found."""
    for directory in (start, *start.parents):
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def minimum_python_version(file_path: str) -> tuple[int, int] | None:
    """The lowest Python version (major, minor) that the nearest `pyproject.toml` above
    `file_path` guarantees, based on its `requires-python`. Returns None if no
    pyproject.toml is found, `requires-python` is missing or unparsable, or no version in
    KNOWN_PYTHON_VERSIONS satisfies the specifier - callers should treat None as "unknown",
    not as "no constraint".
    """
    pyproject_path = find_nearest_pyproject(Path(file_path).resolve().parent)
    if pyproject_path is None:
        return None

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return None

    requires_python = data.get("project", {}).get("requires-python")
    if not isinstance(requires_python, str):
        return None

    try:
        spec = SpecifierSet(requires_python)
    except InvalidSpecifier:
        return None

    for version in KNOWN_PYTHON_VERSIONS:
        if spec.contains(version, prereleases=True):
            major, minor = version.split(".")
            return (int(major), int(minor))
    return None

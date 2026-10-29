# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Guard rail that requires every repository path named in the documentation, the code and the tests to exist.

A path is a name that starts with a top-level directory of the repository followed by `/`, such as `src/renaissance/` or
`docs/index.md`. The check reads the Markdown files in `docs/`, the comments and docstrings of the Python files in `src/`, `test/`,
`tools/` and `features/`, and the feature files. A path that does not exist fails the check, so a file that moves or disappears
cannot leave a reference behind.

The check skips the target of a Markdown link, which `mkdocs build --strict` checks; a path with a placeholder or a wildcard,
which names no single file; and an example, a path with `example` as one of its words, such as `tools/example.py`.

`[tool.check_references]` of `pyproject.toml` lists the files that are not read, and the paths that are known to be missing.
An entry that no longer applies fails the check, so these lists only shrink.

Run `python -m tools.check_references` locally, or `python -m tools.check_references --check` as CI does; both report and
neither writes.
"""

import argparse
import ast
import io
import itertools
import re
import sys
import tokenize
import tomllib
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from tools.shared.repository_files import list_files, with_directories

ROOT = Path(__file__).resolve().parents[1]

DOCUMENTATION_DIRECTORY = "docs"
PYTHON_DIRECTORIES = ("src", "test", "tools", "features")

# The keys of [tool.check_references] that list paths known to be missing, each for its own reason.
MISSING_LISTS = ("known_issues", "stale")

# A placeholder such as {path} or <name>, a wildcard or an ellipsis makes a name a pattern rather than a path.
PATTERN_MARKERS = ("<", ">", "{", "}", "*", "...")
EXAMPLE_WORD = "example"
WORD_SEPARATORS = re.compile(r"[/_.\-]")

MARKDOWN_LINK_TARGET = re.compile(r"\]\([^)]*\)")
MARKDOWN_LINK_DEFINITION = re.compile(r"^\s*\[[^\]]+\]:\s*\S")

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_TOOL_FAILURE = 2


class ConfigError(ValueError):
    """`[tool.check_references]` is invalid."""


@dataclass(frozen=True)
class Config:
    """The files that are not read, and the paths that are known to be missing, per list."""

    exclude: frozenset[str]
    missing: Mapping[str, frozenset[str]]


@dataclass(frozen=True, order=True)
class Reference:
    """A path named on a line of a file."""

    file: str
    line: int
    path: str


@dataclass(frozen=True)
class Violation:
    """A reference or a configuration entry that breaks the rule, and why."""

    location: str
    reason: str

    def describe(self) -> str:
        """Return one line naming the location and what is wrong with it."""
        return f"{self.location}: {self.reason}"


def _strings(config: Mapping[str, object], key: str) -> frozenset[str]:
    """Return the list of strings `config[key]`, or raise when it is something else."""
    value = config.get(key, [])
    items = cast("list[object]", value) if isinstance(value, list) else None
    if items is None or not all(isinstance(item, str) for item in items):
        message = f"`{key}` must be a list of strings"
        raise ConfigError(message)
    strings = cast("list[str]", items)
    if len(set(strings)) != len(strings):
        message = f"`{key}` lists an entry twice"
        raise ConfigError(message)
    return frozenset(strings)


def parse_config(config: Mapping[str, object]) -> Config:
    """Return the `[tool.check_references]` table `config`, or raise `ConfigError` when it is invalid."""
    unknown = set(config) - {"exclude", *MISSING_LISTS}
    if unknown:
        message = f"unknown key(s) {sorted(unknown)} in [tool.check_references]"
        raise ConfigError(message)
    missing = {key: _strings(config, key) for key in MISSING_LISTS}
    for first, second in itertools.combinations(MISSING_LISTS, 2):
        both = missing[first] & missing[second]
        if both:
            message = f"`{first}` and `{second}` both list {sorted(both)}"
            raise ConfigError(message)
    return Config(_strings(config, "exclude"), missing)


def load_config(pyproject: Path) -> Mapping[str, object]:
    """Return the `[tool.check_references]` table of `pyproject`."""
    with pyproject.open("rb") as file:
        return tomllib.load(file).get("tool", {}).get("check_references", {})


def is_read(file: str, exclude: Iterable[str]) -> bool:
    """Return whether the check reads `file`: by its kind and directory, unless `exclude` names it or a directory above it."""
    if any(file == entry or (entry.endswith("/") and file.startswith(entry)) for entry in exclude):
        return False
    top = file.split("/", 1)[0]
    if file.endswith(".md"):
        return top == DOCUMENTATION_DIRECTORY
    if file.endswith(".py"):
        return top in PYTHON_DIRECTORIES
    return file.endswith(".feature")


def markdown_texts(content: str) -> Iterator[tuple[int, str]]:
    """Yield each line of a Markdown file with its number, without the targets of its links."""
    for number, line in enumerate(content.splitlines(), 1):
        if not MARKDOWN_LINK_DEFINITION.match(line):
            yield number, MARKDOWN_LINK_TARGET.sub("]()", line)


def python_texts(content: str) -> Iterator[tuple[int, str]]:
    """Yield each comment and each line of each docstring of a Python file with its line number."""
    try:
        for token in tokenize.generate_tokens(io.StringIO(content).readline):
            if token.type == tokenize.COMMENT:
                yield token.start[0], token.string
    except tokenize.TokenError, SyntaxError:
        pass
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                for offset, line in enumerate(first.value.value.splitlines()):
                    yield first.lineno + offset, line


def texts(file: str, content: str) -> Iterator[tuple[int, str]]:
    """Yield the numbered lines of `file` in which the check looks for paths."""
    if file.endswith(".md"):
        return markdown_texts(content)
    if file.endswith(".py"):
        return python_texts(content)
    return enumerate(content.splitlines(), 1)


def path_pattern(top_level_directories: Iterable[str]) -> re.Pattern[str]:
    """Return the pattern of a name that starts with one of `top_level_directories` followed by `/`."""
    alternatives = "|".join(re.escape(directory) for directory in sorted(top_level_directories))
    return re.compile(rf"(?<![\w./\-])(?:{alternatives})/[\w./\-<>{{}}*]*")


def find_references(contents: Mapping[str, str], top_level_directories: Iterable[str]) -> list[Reference]:
    """Return the paths named in `contents`, which maps each file that is read to its content."""
    pattern = path_pattern(top_level_directories)
    references: set[Reference] = set()
    for file, content in contents.items():
        for number, text in texts(file, content):
            for match in pattern.finditer(text):
                path = match.group().rstrip(".,:;")
                if not any(marker in path for marker in PATTERN_MARKERS):
                    references.add(Reference(file, number, path))
    return sorted(references)


def exists(path: str, paths: set[str]) -> bool:
    """Return whether `path` is one of `paths`, the files and directories, with or without its trailing `/`."""
    return path in paths or f"{path.rstrip('/')}/" in paths


def is_example(path: str) -> bool:
    """Return whether `path` has `example` as one of its words, such as `tools/example.py` or `src/example_package/`."""
    return EXAMPLE_WORD in WORD_SEPARATORS.split(path)


def check(references: Iterable[Reference], paths: set[str], config: Config) -> list[Violation]:
    """Return the references to missing paths that no list records, and the entries of `config` that no longer apply."""
    known = set[str]().union(*config.missing.values())
    named: set[str] = set()
    violations: list[Violation] = []
    for reference in sorted(references):
        if exists(reference.path, paths) or is_example(reference.path):
            continue
        named.add(reference.path)
        if reference.path not in known:
            violations.append(Violation(f"{reference.file}:{reference.line}", f"names {reference.path}, which does not exist"))
    for key, missing in config.missing.items():
        for path in sorted(missing):
            if exists(path, paths):
                violations.append(Violation(path, f"is listed in `{key}`, but exists: remove it"))
            elif path not in named:
                violations.append(Violation(path, f"is listed in `{key}`, but is named nowhere: remove it"))
    violations += [
        Violation(path, "is listed in `exclude`, but does not exist: remove it")
        for path in sorted(config.exclude)
        if not exists(path, paths)
    ]
    return violations


def main(argv: list[str] | None = None) -> int:
    """Report the references to paths that do not exist, and fail on any of them."""
    parser = argparse.ArgumentParser(description="Check that every repository path named in the docs, code and tests exists.")
    # --check mirrors tools/lint_budget.py; this check never writes, so it only documents the CI invocation.
    parser.add_argument("--check", action="store_true", help="only report, never write (used by CI; this check never writes)")
    parser.parse_args(argv)

    try:
        config = parse_config(load_config(ROOT / "pyproject.toml"))
        files = list_files(ROOT)
        contents = {file: (ROOT / file).read_text(encoding="utf-8") for file in sorted(files) if is_read(file, config.exclude)}
    except (ConfigError, OSError, RuntimeError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        print(f"Could not check the references in {ROOT}: {error}", file=sys.stderr)  # noqa: T201 (a script reports on stdout and stderr)
        return EXIT_TOOL_FAILURE
    references = find_references(contents, {file.split("/", 1)[0] for file in files if "/" in file})
    violations = check(references, with_directories(files), config)

    if violations:
        report = ["These references name a missing path, or these entries of [tool.check_references] no longer apply:"]
        report += [f"  {violation.describe()}" for violation in violations]
        report.append(
            "\nCorrect the reference, or record the missing path in [tool.check_references] of pyproject.toml;"
            " see docs/developer/tools/check-references.md."
        )
    else:
        known = sum(len(missing) for missing in config.missing.values())
        report = [f"Reference check passed: {len(references)} reference(s) in {len(contents)} file(s), {known} known missing path(s)."]
    print("\n".join(report))  # noqa: T201 (a script reports on stdout and stderr)

    return EXIT_VIOLATIONS if violations else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

"""Guard rail that forbids imports crossing a layer boundary.

The source tree is divided into layers. Each layer may only import the layers below it:
the core is language- and parser-agnostic and may not depend on anything else, parser
bindings and recipes build on the core, and the application code may use all of them.
Keeping the core free of such dependencies is what makes a parser binding replaceable.

This script parses every module under `src/` and reports each import that crosses a
boundary in the wrong direction. Violations that are known and accepted for now are listed
in `ALLOWLIST`, together with the reason; an allowlist entry that no longer matches a real
violation fails the check as well, so the allowlist cannot outlive the problem it describes.

Run `python tools/check_layering.py` locally, or `python tools/check_layering.py --check`
as CI does; both report and neither writes.
"""

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"

# The packages each layer owns. Renaming a package is a one-line edit here.
LAYERS: dict[str, tuple[str, ...]] = {
    "core": ("renaissance.syntax_tree", "renaissance.common", "renaissance.utils"),
    "parser_bindings": ("renaissance.integrations",),
    "recipes": ("renaissance.recipes", "rejuvenation"),
}

# The other layers each layer may import; importing within a layer is always allowed.
ALLOWED_DEPENDENCIES: dict[str, frozenset[str]] = {
    "core": frozenset(),
    "parser_bindings": frozenset({"core"}),
    "recipes": frozenset({"core", "parser_bindings"}),
}

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_TOOL_FAILURE = 2


@dataclass(frozen=True)
class Exemption:
    """A known violation that is reported but does not fail the check yet."""

    module: str
    imported: str
    reason: str


ALLOWLIST: tuple[Exemption, ...] = (
    Exemption(
        module="renaissance.syntax_tree",
        imported="renaissance.integrations.clang.cpp_utils",
        reason="re-export of CPPUtils; the import is deliberately late to break a circular import (issue 110)",
    ),
    Exemption(
        module="renaissance.syntax_tree.ast_refactor_actions",
        imported="renaissance.integrations.clang.c_pattern_factory",
        reason="CPPPatternFactory is used in a type annotation only; the core needs a parser-agnostic pattern type (issue 110)",
    ),
    Exemption(
        module="renaissance.utils.ast_utils",
        imported="renaissance.integrations",
        reason="MATCH_ALL and MATCH_ONE are placeholder markers that belong in the core, not in the bindings (issue 110)",
    ),
)


@dataclass(frozen=True)
class ImportSite:
    """An import statement found in a module."""

    module: str
    line: int
    type_checking_only: bool


@dataclass(frozen=True)
class Violation:
    """An import that crosses a layer boundary in a direction that is not allowed."""

    module: str
    imported: str
    source_layer: str
    target_layer: str
    path: Path
    line: int
    type_checking_only: bool

    def describe(self, relative_to: Path) -> str:
        """Return a one-line report naming the file and line, so terminals can link to it."""
        suffix = " [type-checking only]" if self.type_checking_only else ""
        location = self.path.relative_to(relative_to) if self.path.is_relative_to(relative_to) else self.path
        return f"{location}:{self.line}: {self.module} ({self.source_layer}) imports {self.imported} ({self.target_layer}){suffix}"


def module_name(path: Path, source_root: Path) -> str:
    """Return the dotted module name of `path`, which lies inside `source_root`."""
    parts = path.relative_to(source_root).with_suffix("").parts
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def layer_of(module: str) -> str | None:
    """Return the layer that owns `module`, or None when no layer claims it."""
    for layer, packages in LAYERS.items():
        if any(module == package or module.startswith(f"{package}.") for package in packages):
            return layer
    return None


def resolve_import(name: str | None, package: str, level: int) -> str:
    """Return the absolute module name of an import of `name` written inside `package`."""
    if not level:
        return name or ""
    parts = package.split(".") if package else []
    prefix = ".".join(parts[: max(len(parts) - level + 1, 0)])
    if not prefix:
        return name or ""
    return f"{prefix}.{name}" if name else prefix


def _is_type_checking_test(test: ast.expr) -> bool:
    """Return whether `test` is the `TYPE_CHECKING` condition of a type-checking-only block."""
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def iter_import_sites(nodes: Iterable[ast.AST], package: str, *, type_checking: bool) -> Iterator[ImportSite]:
    """Yield every import below `nodes`, including those nested in functions and in `if TYPE_CHECKING` blocks."""
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield ImportSite(alias.name, node.lineno, type_checking)
        elif isinstance(node, ast.ImportFrom):
            yield ImportSite(resolve_import(node.module, package, node.level), node.lineno, type_checking)
        elif isinstance(node, ast.If) and _is_type_checking_test(node.test):
            yield from iter_import_sites(node.body, package, type_checking=True)
            yield from iter_import_sites(node.orelse, package, type_checking=type_checking)
        else:
            yield from iter_import_sites(ast.iter_child_nodes(node), package, type_checking=type_checking)


def violations_in(path: Path, source_root: Path) -> list[Violation]:
    """Return the layering violations of the single module at `path`."""
    module = module_name(path, source_root)
    source_layer = layer_of(module)
    if source_layer is None:
        return []
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    allowed = ALLOWED_DEPENDENCIES.get(source_layer, frozenset())
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[Violation] = []
    for site in iter_import_sites(tree.body, package, type_checking=False):
        target_layer = layer_of(site.module)
        if target_layer is None or target_layer == source_layer or target_layer in allowed:
            continue
        violations.append(
            Violation(
                module=module,
                imported=site.module,
                source_layer=source_layer,
                target_layer=target_layer,
                path=path,
                line=site.line,
                type_checking_only=site.type_checking_only,
            )
        )
    return violations


def find_violations(source_root: Path) -> list[Violation]:
    """Return every layering violation below `source_root`, ordered by file and line."""
    violations: list[Violation] = []
    for path in sorted(source_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        violations += violations_in(path, source_root)
    return sorted(violations, key=lambda violation: (str(violation.path), violation.line))


def exemption_for(violation: Violation) -> Exemption | None:
    """Return the allowlist entry that covers `violation`, or None when it is not exempted."""
    for exemption in ALLOWLIST:
        if exemption.module == violation.module and exemption.imported == violation.imported:
            return exemption
    return None


def stale_exemptions(violations: Iterable[Violation]) -> list[Exemption]:
    """Return the allowlist entries that no longer match a violation, so they can be deleted."""
    matched = {(violation.module, violation.imported) for violation in violations}
    return [exemption for exemption in ALLOWLIST if (exemption.module, exemption.imported) not in matched]


def main(argv: list[str] | None = None) -> int:
    """Report the layering violations under `src/` and fail on any that is not allowlisted."""
    parser = argparse.ArgumentParser(description="Check that the imports in src/ respect the layer boundaries.")
    # --check mirrors tools/lint_budget.py; this check never writes, so it only documents the CI invocation.
    parser.add_argument("--check", action="store_true", help="only report, never write (used by CI; this check never writes)")
    parser.parse_args(argv)

    try:
        violations = find_violations(SOURCE_ROOT)
    except (OSError, SyntaxError) as error:
        print(f"Could not analyse {SOURCE_ROOT}: {error}", file=sys.stderr)  # noqa: T201 (a script reports on stdout and stderr)
        return EXIT_TOOL_FAILURE

    forbidden = [violation for violation in violations if exemption_for(violation) is None]
    exempted = [violation for violation in violations if exemption_for(violation) is not None]
    stale = stale_exemptions(violations)

    report: list[str] = []
    if exempted:
        report.append("Allowlisted layering violations (to be resolved, not to be extended):")
        report += [f"  {violation.describe(ROOT)}" for violation in exempted]
    if forbidden:
        report.append("\nThese imports cross a layer boundary that is not allowed:")
        report += [f"  {violation.describe(ROOT)}" for violation in forbidden]
        report.append("\nImport through an abstraction of the layer below instead, or ask for an allowlist entry.")
    if stale:
        report.append("\nThese allowlist entries no longer match a violation and must be deleted from tools/check_layering.py:")
        report += [f"  {exemption.module} -> {exemption.imported}" for exemption in stale]
    if not forbidden and not stale:
        report.append(f"Layering check passed: {len(exempted)} allowlisted violation(s), no new ones.")
    print("\n".join(report))  # noqa: T201 (a script reports on stdout and stderr)

    return EXIT_VIOLATIONS if forbidden or stale else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

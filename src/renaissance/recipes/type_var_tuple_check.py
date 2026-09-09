"""Recipe modernizing legacy `Unpack[T]` usage of a declared TypeVarTuple to native `*T` syntax."""

import ast
from typing import cast

from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.type_var_domain import find_type_param_declarations, type_param_constructor_name
from renaissance.utils.python_version import minimum_python_version

PEP_646_MINIMUM = (3, 11)


def target_supports_pep646(file_path: str) -> bool:
    """Return True only if the target codebase's minimum supported Python version is 3.11+.

    See renaissance.utils.python_version.minimum_python_version. Conservative by design: an
    unknown minimum (no pyproject.toml, no/unparsable requires-python, or a version below 3.11)
    all return False - native `*T` unpacking syntax (PEP 646) is a hard SyntaxError before Python
    3.11, so an unknown minimum must never be treated as safe.
    """
    minimum = minimum_python_version(file_path)
    return minimum is not None and minimum >= PEP_646_MINIMUM


class TypeVarTupleCheck(PythonRefactoring):
    """Modernize legacy `Unpack[T]` usage of a declared TypeVarTuple to native `*T` syntax.

    See fix_legacy_unpack_usage() for the rewrite this runs; find_legacy_unpack_usage() alone still
    just detects, kept for any caller that only wants the names without touching the file.
    """

    # Set directly (e.g. in a test) to skip the pyproject.toml lookup and use this value instead -
    # mirrors how TypeVarCheck.min_python_override/in_memory are set on a recipe after construction.
    min_python_override: tuple[int, int] | None = None

    def run(self) -> None:
        """Entry point called by PythonRefactoring.process(); stores fix_legacy_unpack_usage()'s result."""
        self.result = self.fix_legacy_unpack_usage()
        if "fixed" in self.result.values():
            self.commit()

    def _target_supports_pep646(self) -> bool:
        """Return True if native `*T` unpacking syntax is safe on this recipe's target file.

        Uses min_python_override if a test set one, otherwise target_supports_pep646(self.filename).
        """
        if self.min_python_override is not None:
            return self.min_python_override >= PEP_646_MINIMUM
        return target_supports_pep646(self.filename)

    def find_legacy_unpack_usage(self) -> list[str]:
        """Find every module-level TypeVarTuple name still referenced via the legacy Unpack[T] subscript form.

        The newer syntax is `*T` unpacking instead. Detection only - see fix_legacy_unpack_usage()
        to actually rewrite these.
        """
        tree = cast("ast.Module", self.root.node)
        return [name for name, _ in self._find_unpack_occurrences(tree)]

    def fix_legacy_unpack_usage(self) -> dict[str, str]:
        """Rewrite every legacy `Unpack[T]` usage of a declared TypeVarTuple to native `*T` syntax.

        `Unpack[T]` and `*T` are fully equivalent wherever T is a TypeVarTuple - Unpack exists only
        because it's parseable on Pythons before the native syntax landed (PEP 646, 3.11+), so
        there's no per-occurrence safety analysis needed beyond the file-wide version gate: if the
        target doesn't declare 3.11+, every candidate is reported "unsafe" and the file is left
        untouched. Returns {name: "fixed" | "unsafe"}.
        """
        tree = cast("ast.Module", self.root.node)
        occurrences = self._find_unpack_occurrences(tree)
        if not occurrences:
            return {}

        names = {name for name, _ in occurrences}
        if not self._target_supports_pep646():
            return dict.fromkeys(names, "unsafe")

        for name, node in occurrences:
            rst_node = self.find_rst_node(node)
            self.replace(f"*{name}", rst_node, include_whitespace=False, include_comments=False)

        return dict.fromkeys(names, "fixed")

    def _find_unpack_occurrences(self, tree: ast.Module) -> list[tuple[str, ast.Subscript]]:
        """Find every `Unpack[name]` subscript in the file where `name` is a declared TypeVarTuple.

        Returns (name, node) pairs, one per occurrence - the same name can appear more than once.
        """
        declarations = find_type_param_declarations(tree)
        typevartuple_names = {name for name, decl in declarations.items() if type_param_constructor_name(decl) == "TypeVarTuple"}

        return [
            (node.slice.id, node)
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id == "Unpack"
                and isinstance(node.slice, ast.Name)
                and node.slice.id in typevartuple_names
            )
        ]

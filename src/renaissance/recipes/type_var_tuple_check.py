"""Recipe flagging legacy `Unpack[T]` usage of a declared TypeVarTuple."""

import ast
from typing import cast

from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.type_var_domain import find_type_param_declarations, type_param_constructor_name


class TypeVarTupleCheck(PythonRefactoring):
    """Flags module-level TypeVarTuple declarations still referenced via the legacy `Unpack[T]` form.

    The newer syntax is `*T` unpacking instead. Reports only, doesn't rewrite.
    """

    def run(self) -> None:
        """Entry point called by PythonRefactoring.process(); stores find_legacy_unpack_usage()'s result."""
        self.result = self.find_legacy_unpack_usage()

    def find_legacy_unpack_usage(self) -> list[str]:
        """Find every module-level TypeVarTuple name still referenced via the legacy Unpack[T] subscript form.

        The newer syntax is `*T` unpacking instead.
        """
        tree = cast(ast.Module, self.root.node)
        declarations = find_type_param_declarations(tree)
        typevartuple_names = {name for name, decl in declarations.items() if type_param_constructor_name(decl) == "TypeVarTuple"}

        found: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "Unpack"
                    and isinstance(node.slice, ast.Name)
                    and node.slice.id in typevartuple_names
                ):
                    found.append(node.slice.id)

        return found

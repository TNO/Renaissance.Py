import ast
from typing import cast

from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.refactoring.type_var_check import find_type_param_declarations, type_param_constructor_name


class TypeVarTupleCheck(PythonRefactoring):
    def run(self) -> None:
        self.result = self.find_legacy_unpack_usage()

    def find_legacy_unpack_usage(self) -> list[str]:
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
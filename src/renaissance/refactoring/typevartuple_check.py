import ast
from typing import cast

from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.refactoring.typevar_check import find_type_param_declarations
from renaissance.utils.ast_utils import traverse


class TypeVarTupleCheck(PythonRefactoring):
    def run(self) -> None:
        self.result = self.find_legacy_unpack_usage()

    def find_legacy_unpack_usage(self) -> list[str]:
        declarations = find_type_param_declarations(self.root)
        typevartuple_names = {name for name, kind in declarations.items() if kind == "TypeVarTuple"}

        found: list[str] = []
        for node in traverse(self.root):
            raw = cast(ast.AST, node.node)
            if isinstance(raw, ast.Subscript):
                if (
                    isinstance(raw.value, ast.Name)
                    and raw.value.id == "Unpack"
                    and isinstance(raw.slice, ast.Name)
                    and raw.slice.id in typevartuple_names
                ):
                    found.append(raw.slice.id)

        return found
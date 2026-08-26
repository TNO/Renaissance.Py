import ast
from typing import cast

from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.utils.ast_utils import traverse

def get_enclosing_function(node):
    current = node.parent
    while current:
        if current.ast_type.__name__ == "FunctionDef":
            return current
        current = current.parent
    return None

class TypeVarCheck(PythonRefactoring):
    def run(self):
        self.result = self.find_multi_scope_typevars()

    def find_multi_scope_typevars(self):
        typevar_names = []
        for node in traverse(self.root):
            raw = cast(ast.AST, node.node)
            if isinstance(raw, ast.Assign):
                value = raw.value
                if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "TypeVar":
                    for target in raw.targets:
                        if isinstance(target, ast.Name):
                            typevar_names.append(target.id)

        results = {}
        for name in typevar_names:
            functions = set()
            for node in traverse(self.root):
                if node.name == name:
                    func = get_enclosing_function(node)
                    if func:
                        functions.add(func.name)
            results[name] = functions

        return {name: funcs for name, funcs in results.items() if len(funcs) > 1}
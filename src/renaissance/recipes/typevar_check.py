import ast
from typing import cast

from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.utils.ast_utils import traverse

def get_enclosing_function(node):
    # Walk up from this node to the nearest enclosing FunctionDef
    current = node.parent
    while current:
        if current.ast_type.__name__ == "FunctionDef":
            return current
        current = current.parent
    return None

def find_type_param_declarations(root):
    # Find and collect every "X = TypeVar/ParamSpec/TypeVarTuple"
    declarations = {}
    for node in traverse(root):
        raw = cast(ast.AST, node.node)
        if isinstance(raw, ast.Assign):
            value = raw.value
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in ("TypeVar", "ParamSpec", "TypeVarTuple"):
                for target in raw.targets:
                    if isinstance(target, ast.Name):
                        declarations[target.id] = value.func.id
    return declarations

class TypeVarCheck(PythonRefactoring):
    def run(self):
        self.result = self.find_multi_scope_typevars()

    def find_multi_scope_typevars(self):
        # Only flag names shared across 2+ functions
        # Ruff can't safely decide what to do if typevars are reused across functions
        # This function only detects and reports them
        typevar_names = find_type_param_declarations(self.root).keys()

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
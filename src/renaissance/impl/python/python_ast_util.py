import textwrap

from renaissance.impl.python.python_ast_node import PythonASTNode


def raw(nodes: PythonASTNode):
    res = ""
    for node in nodes:
        res += "\n\n    " + node.text
    return res + "\n    "


def to_str(node: PythonASTNode) -> str:
    if hasattr(node, "signature"):
        return node.signature
    else:
        return str(node)


def convert_function(fun):
    signature: str = fun.signature + "\n\n\n"
    if len(fun.node.args.args) == 0:
        signature = signature.replace(f"{fun.name}()", f"{fun.name}(self)", 1)
    else:
        signature = signature.replace(f"{fun.name}(", f"{fun.name}(self,", 1)
    return signature

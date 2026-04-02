
def convert(lines, line_nr, col):
    if line_nr > len(lines):
        return 0
    return sum(len(lines[i]) + 1 for i in range(line_nr - 1)) + col
    # add node to the node list for references


def raw(nodes):
    res = ""
    for node in nodes:
        res += "\n\n    " + node.signature
    return res + "\n    "


def to_str(node) -> str:
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

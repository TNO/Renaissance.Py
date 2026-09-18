"""AI: Utility helpers for converting between source positions and node representations."""


def convert(lines, line_nr, col):
    """AI: Convert a (line, column) source position into an absolute character offset."""
    if line_nr > len(lines):
        return 0
    return sum(len(lines[i]) + 1 for i in range(line_nr - 1)) + col
    # add node to the node list for references


def to_str(node) -> str:
    """AI: Return the node's signature if it has one, otherwise its string representation."""
    if hasattr(node, "signature"):
        return node.signature
    return str(node)


def convert_function(fun):
    """AI: Return the function's signature rewritten to take a leading 'self' parameter."""
    signature: str = fun.signature + "\n\n\n"
    if len(fun.node.args.args) == 0:
        signature = signature.replace(f"{fun.name}()", f"{fun.name}(self)", 1)
    else:
        signature = signature.replace(f"{fun.name}(", f"{fun.name}(self,", 1)
    return signature

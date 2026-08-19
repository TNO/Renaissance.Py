#!/usr/bin/env python3
"""
Pretty-print a Python AST with indentation reflecting node depth.

Usage:
  - As a library:
        from ast_tree_printer import print_ast_tree
        import ast
        tree = ast.parse("x = 1 + f(y)")
        print_ast_tree(tree, show_positions=True)

  - As a script:
        python ast_tree_printer.py path/to/code.py
        # or:
        echo "def f(x): return x*x" | python ast_tree_printer.py -
"""

import ast
import sys
from typing import Any, Iterable, Tuple

# --- Helpers to extract small, readable summaries for leaf-ish nodes ---

def _const_repr(value: Any) -> str:
    # Compact representation for constants
    try:
        return repr(value)
    except Exception:
        return f"<unreprable {type(value).__name__}>"

def _node_headline(n: ast.AST) -> str:
    """
    Build a compact, one-line summary of a node's key attributes (if any).
    Examples:
      Name(id='x'), Constant(value=42), Attribute(value=..., attr='foo'), arg='x'
    """
    parts : list[str] = []

    # Commonly useful fields to surface inline if present:
    interesting_scalar_fields = (
        "id", "arg", "attr", "name", "module", "asname"
    )

    # Constants across Python versions:
    # - Py3.8+: Constant(value=...)
    # - Older nodes like Num/Str/NameConstant are folded into Constant in modern Python.
    if isinstance(n, ast.Constant):
        parts.append(f"value={_const_repr(n.value)}")
    elif isinstance(n, ast.alias):
        # used in imports
        if getattr(n, "asname", None) is not None:
            parts.append(f"name={n.name!r}, asname={n.asname!r}")
        else:
            parts.append(f"name={n.name!r}")
    else:
        for f in interesting_scalar_fields:
            if hasattr(n, f):
                v = getattr(n, f)
                if isinstance(v, str):
                    parts.append(f"{f}={v!r}")
                elif isinstance(v, (int, float, bool, type(None))):
                    parts.append(f"{f}={v!r}")

    # Optional: show operator kinds (e.g., Add, Sub) for operator wrapper nodes
    # e.g., BinOp(op=Add), UnaryOp(op=Not)
    if isinstance(n, ast.BinOp):
        parts.append(f"op={type(n.op).__name__}")
    elif isinstance(n, ast.BoolOp):
        parts.append(f"op={type(n.op).__name__}")
    elif isinstance(n, ast.UnaryOp):
        parts.append(f"op={type(n.op).__name__}")
    elif isinstance(n, ast.Compare):
        parts.append("ops=" + ",".join(type(op).__name__ for op in n.ops))
    elif isinstance(n, ast.Assign):
        if getattr(n, "type_comment", None):
            parts.append(f"type_comment={n.type_comment!r}")
    elif isinstance(n, ast.AnnAssign):
        parts.append(f"simple={getattr(n, 'simple', '?')}")
    elif isinstance(n, ast.ImportFrom):
        # level can be 0 or None or more (for relative imports)
        lvl = getattr(n, "level", None)
        parts.append(f"level={lvl!r}")

    if parts:
        return f"{type(n).__name__}(" + ", ".join(parts) + ")"
    else:
        return type(n).__name__

def _iter_children(n: ast.AST) -> Iterable[Tuple[str, Any]]:
    """
    Yield (field_name, value) for all fields of the node, so we can traverse
    lists and nested nodes. Skips None fields automatically.
    """
    for field, value in ast.iter_fields(n):
        if value is None:
            continue
        yield field, value

def print_ast_tree(node: ast.AST, indent: int = 0, show_positions: bool = False, _prefix: str = "") -> None:
    """
    Pretty-print the AST with indentation related to node depth.

    Parameters
    ----------
    node : ast.AST
        The AST node to print.
    indent : int
        Current indentation level (in spaces).
    show_positions : bool
        If True, include lineno/col_offset and end_lineno/end_col_offset (if available).
    _prefix : str
        Internal: label for the edge into this node (e.g., the field name on the parent).
    """
    IND = "  " * indent
    head = _node_headline(node)

    pos = ""
    if show_positions:
        # location fields may or may not exist depending on the node and Python version
        fields : list[str] = []
        if hasattr(node, "lineno") and hasattr(node, "col_offset"):
            fields.append(f"{node.lineno}:{node.col_offset}")
        if hasattr(node, "end_lineno") and hasattr(node, "end_col_offset"):
            fields.append(f"{node.end_lineno}:{node.end_col_offset}")
        if fields:
            if len(fields) == 1:
                pos = f" [@{fields[0]}]"
            else:
                pos = f" [@{fields[0]}→{fields[1]}]"

    if _prefix:
        print(f"{IND}{_prefix}: {head}{pos}")
    else:
        print(f"{IND}{head}{pos}")

    # Traverse children
    for field, value in _iter_children(node):
        if isinstance(value, ast.AST):
            print_ast_tree(value, indent + 1, show_positions, _prefix=field)
        elif isinstance(value, list):
            if not value:
                continue
            print(f"{IND}  {field}: [")
            for i, item in enumerate(value):
                if isinstance(item, ast.AST):
                    # index label helps disambiguate multiple items under same field
                    print_ast_tree(item, indent + 2, show_positions, _prefix=f"{i}")
                else:
                    # non-AST items in lists (uncommon, but safe to handle)
                    print(f"{IND}    {i}: {item!r}")
            print(f"{IND}  ]")
        else:
            # Scalar child fields—print compactly on one line
            print(f"{IND}  {field}: {value!r}")


def main(argv: list[str]) -> int:
    examples : list[tuple[str, list[str]]] = [
        ("function definitions" , [
"""
def standard_arg(arg):
    pass
""",
"""
def standard_arg_with_type(arg : int):
    pass
""",
"""
def standard_arg_with_default(arg = 3):
    pass
""",
"""
def standard_arg_with_type_with_default(arg : int = 3):
    pass
""",
"""
def standard_args(arg1, arg2):
    pass
""",
"""
def pos_only_arg(arg, /):
    pass
""",
"""
def pos_only_arg_with_type(arg : int, /):
    pass
""",
"""
def pos_only_arg_with_default(arg = 3, /):
    pass
""",
"""
def pos_only_arg_with_type_with_default(arg : int = 3, /):
    pass
""",
"""
def pos_only_args(arg1, arg2, /):
    pass
""",
"""
def kwd_only_arg(*, arg):
    pass
""",
"""
def kwd_only_arg_with_type(*, arg : int):
    pass
""",
"""
def kwd_only_arg_with_default(*, arg = 3):
    pass
""",
"""
def kwd_only_arg_with_type_with_default(*, arg: int = 3):
    pass
""",
"""
def kwd_only_args(*, arg1, arg2):
    pass
""",
"""
def combined_example(pos_only, /, standard, *, kwd_only):
    pass
""",
"""
def with_typehints(arg: type) -> return_type:
    pass
"""
        ])
    ]


    for description, codes in examples:
        print("==========================================================")
        print(description)

        for code in codes:
            print("---------------------------------------------------------------")
            print(code)
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                sys.stderr.write(f"SyntaxError: {e}\n")
                return 2
            print_ast_tree(tree, show_positions=True)
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

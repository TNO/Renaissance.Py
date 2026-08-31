"""Workaround for a shared rewrite-pipeline bug (python-ast-known-limitations.md item 4).

TextUtils.shift_right double-indents a docstring's continuation lines when ast.unparse() output
for a whole function/class replaces the original node, since those lines already carry their own
correct indentation. Any recipe doing a whole-node ast.unparse()-based replacement needs this.
"""

import ast
from typing import cast


def normalize_docstring_indent(value: str, target_indent: int = 4) -> str:
    """Reset a docstring's continuation lines to one canonical indent.

    So the shift TextUtils applies afterwards lands each line at the right depth instead of
    compounding on top of it.
    """
    lines = value.split("\n")
    if len(lines) < 2:
        return value  # single-line docstring - nothing to double-indent
    body = lines[1:]
    non_blank = [line for line in body if line.strip()]
    if not non_blank:
        return value
    common = min(len(line) - len(line.lstrip(" ")) for line in non_blank)
    prefix = " " * target_indent
    result = [lines[0]]
    for i, line in enumerate(body):
        content = line[common:] if common else line
        is_last = i == len(body) - 1
        # rstrip (not strip) preserves each line's own indentation *relative* to `common` -
        # e.g. a nested list inside the docstring stays nested, not flattened to one level.
        result.append(prefix + content.rstrip() if (content.strip() or is_last) else "")
    return "\n".join(result)


def unparse_node(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> str:
    """Like ast.unparse(), but first normalizes node's docstring indent.

    See normalize_docstring_indent - this is what keeps a whole-node replacement from
    double-indenting it.
    """
    docstring = ast.get_docstring(node, clean=False)
    if docstring is not None and "\n" in docstring:
        cast(ast.Constant, cast(ast.Expr, node.body[0]).value).value = normalize_docstring_indent(docstring)
    return ast.unparse(node)

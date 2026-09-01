"""Signature-only replacement for whole-node ast.unparse() rewrites.

Regenerating a function's entire body from the AST (plain ast.unparse()) loses anything the AST
doesn't capture - comments, most notably, since Python's ast module never records them at all -
and reformats whatever it does capture to ast.unparse()'s own style. Splicing a freshly-unparsed
header onto the function's original, untouched body avoids both: nothing not on the signature
line ever gets regenerated.
"""

import ast
import io
import tokenize


def _header_end_position(source: str, start_line: int = 1) -> tuple[int, int]:
    """Return the (line, col) right after a def/class header's terminating ':'.

    Both are relative to `source`, line 1-indexed. Tracks ([{/)]} bracket depth so a colon
    inside a string default, a lambda default, or an annotation - anything not at the header's
    own top level - isn't mistaken for the real one.
    """
    text = "\n".join(source.split("\n")[start_line - 1 :])
    depth = 0
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.OP and tok.string in "([{":
            depth += 1
        elif tok.type == tokenize.OP and tok.string in ")]}":
            depth -= 1
        elif tok.type == tokenize.OP and tok.string == ":" and depth == 0:
            return start_line - 1 + tok.end[0], tok.end[1]
    raise ValueError("no header-terminating ':' found")


def unparse_signature_only(node: ast.FunctionDef | ast.AsyncFunctionDef, original_text: str) -> str:
    """Regenerate only node's signature line(s) via ast.unparse(), keeping its original body.

    `original_text` is node's own source text before any mutation (e.g.
    `self.find_rst_node(node).text`, captured before appending to node.type_params) - the body
    spliced back on is that exact original text, comments and formatting included: unchanged if
    it sits inline on the header's own line (e.g. `def f(x): ...`), otherwise renormalized to a
    4-space baseline (see _renormalize_body_indent) since the rewrite pipeline re-adds node's
    real indentation on top of whatever this returns.
    """
    new_line, new_col = _header_end_position(ast.unparse(node))
    new_lines = ast.unparse(node).split("\n")
    new_header = "\n".join([*new_lines[: new_line - 1], new_lines[new_line - 1][:new_col]])

    original_line, original_col = _header_end_position(original_text)
    original_lines = original_text.split("\n")
    inline_tail = original_lines[original_line - 1][original_col:]
    if inline_tail.strip():
        return new_header + inline_tail

    body_lines = original_lines[original_line:]
    if not body_lines:
        return new_header

    return f"{new_header}\n" + "\n".join(_renormalize_body_indent(body_lines))


def _renormalize_body_indent(body_lines: list[str], target_indent: int = 4) -> list[str]:
    """Shift `body_lines` so their common leading indent becomes `target_indent`.

    `original_text` (see unparse_signature_only) carries the body's real, absolute indentation
    from the source file (e.g. 8 spaces for a method inside a class), but the rewrite pipeline's
    ast_rewriter.py shifts every line but the first by the target position's own indent before
    inserting - matching what ast.unparse() would produce for a body one level under a column-0
    `def`. Left as absolute, the body would be shifted twice and land one level too deep.
    """
    non_blank = [line for line in body_lines if line.strip()]
    if not non_blank:
        return body_lines
    common = min(len(line) - len(line.lstrip(" ")) for line in non_blank)
    shift = common - target_indent
    if shift > 0:
        return [line[shift:] if line.strip() else line for line in body_lines]
    if shift < 0:
        pad = " " * -shift
        return [pad + line if line.strip() else line for line in body_lines]
    return body_lines

"""Splice a PEP 695 type-params bracket into a function's original source, changing nothing else.

`ast.unparse()` can only regenerate a *whole* node's source, and does so in its own style -
reformatting whatever it touches regardless of the original formatting (collapsing a multi-line
parameter list onto one line, among other things), and dropping anything the `ast` module never
records in the first place (comments, most notably). Convert-to-PEP-695 only ever adds a
`[T]`/`[**P]`/`[*Ts]` bracket right after a function's name - splicing just that bracket into the
function's untouched original text avoids regenerating (and so reformatting) anything else.
"""

import ast
import io
import re
import tokenize


def _name_end_offset(source: str, name: str) -> int:
    """Return the character offset right after `def name`/`async def name` in `source`.

    Allows leading whitespace before `def`/`async def` - a decorated function's source has the
    decorator on line 1, so the `def` line itself is a continuation line carrying its own real
    indentation, not necessarily flush at column 0.
    """
    match = re.search(rf"^[ \t]*(async\s+)?def\s+{re.escape(name)}\b", source, re.MULTILINE)
    if match is None:
        raise ValueError(f"no 'def {name}' header found")
    return match.end()


def _bracket_end_offset(source: str, open_offset: int) -> int:
    """Return the offset right after the `]` matching the `[` at `open_offset` in `source`.

    Tracks bracket depth so a bound like `list[int]` nesting inside the type-params bracket
    itself doesn't close it early. Doesn't account for `[`/`]` inside a string literal (e.g. an
    unbalanced bracket in a forward-reference bound) - the type-params bracket is always a single,
    short, compact expression in practice, so that edge case is accepted rather than solved.
    """
    depth = 0
    for offset in range(open_offset, len(source)):
        if source[offset] == "[":
            depth += 1
        elif source[offset] == "]":
            depth -= 1
            if depth == 0:
                return offset + 1
    raise ValueError("no closing ']' found")


def _type_params_bracket(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return the PEP 695 `[...]` bracket text for node's current type_params, or "" if none.

    E.g. `"[T]"`, `"[T: int, **P]"` - whatever `ast.unparse(node)` would produce.
    """
    if not node.type_params:
        return ""
    unparsed = ast.unparse(node)
    start = _name_end_offset(unparsed, node.name)
    end = _bracket_end_offset(unparsed, start)
    return unparsed[start:end]


def _header_end_line(source: str) -> int:
    """Return the 1-indexed line where a def header's terminating ':' sits in `source`.

    Tracks `([{`/`)]}` bracket depth (via `tokenize`) so a colon inside a string default, a
    lambda default, or an annotation - anything not at the header's own top level - isn't
    mistaken for the real one.
    """
    depth = 0
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.OP and tok.string in "([{":
            depth += 1
        elif tok.type == tokenize.OP and tok.string in ")]}":
            depth -= 1
        elif tok.type == tokenize.OP and tok.string == ":" and depth == 0:
            return tok.end[0]
    raise ValueError("no header-terminating ':' found")


def unparse_signature_only(node: ast.FunctionDef | ast.AsyncFunctionDef, original_text: str) -> str:
    """Insert node's PEP 695 type-params bracket into `original_text`, changing nothing else.

    `original_text` is node's own source text from before `node.type_params` was mutated (e.g.
    `self.find_rst_node(node).text`, captured before appending to it). If `original_text` already
    has a bracket right after the function name - the function already declared *other* type
    params before this pass touched it, e.g. `def f[U](x: U, y: T) -> T:` when only `T` is being
    converted - that whole bracket is replaced with the new one (which already includes both the
    old and new params, since `node.type_params` does by the time this runs). Otherwise a fresh
    bracket is inserted.

    Every other byte of `original_text` - parameter list, defaults, line breaks, return type,
    docstring, body, comments - is preserved, though lines after the first are re-indented
    relative to a column-0 `def` (see `_renormalize_indent`): `original_text` carries each line's
    real, absolute indentation from the source file, but the rewrite pipeline
    (`ast_rewriter.py`) re-adds the target's real indentation to every line but the first before
    inserting, so returning absolute indentation here would shift everything twice.
    """
    new_bracket = _type_params_bracket(node)
    insert_at = _name_end_offset(original_text, node.name)

    end = insert_at
    if original_text[insert_at : insert_at + 1] == "[":
        end = _bracket_end_offset(original_text, insert_at)

    spliced = original_text[:insert_at] + new_bracket + original_text[end:]
    lines = spliced.split("\n")
    if len(lines) == 1:
        return spliced

    header_end_line = _header_end_line(spliced)
    header_tail = lines[1:header_end_line]  # a multi-line signature's own continuation lines
    body = lines[header_end_line:]
    # the header's own continuation lines (e.g. a closing ") -> T:") sit at the def's own column,
    # so they renormalize to 0; the body sits one Python indentation level deeper, so 4.
    return "\n".join([lines[0], *_renormalize_indent(header_tail, 0), *_renormalize_indent(body, 4)])


def _renormalize_indent(lines: list[str], target_indent: int) -> list[str]:
    """Shift `lines` so their common leading indent becomes `target_indent`.

    See `unparse_signature_only`'s docstring for why: `original_text` carries each line's real,
    absolute indentation, but the rewrite pipeline re-adds the target's own real indentation on
    top of whatever this returns, so it must be expressed relative to a column-0 `def` first.
    """
    non_blank = [line for line in lines if line.strip()]
    if not non_blank:
        return lines
    common = min(len(line) - len(line.lstrip(" ")) for line in non_blank)
    shift = common - target_indent
    if shift > 0:
        return [line[shift:] if line.strip() else line for line in lines]
    if shift < 0:
        pad = " " * -shift
        return [pad + line if line.strip() else line for line in lines]
    return lines

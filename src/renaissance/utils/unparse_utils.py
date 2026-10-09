"""Splice a PEP 695 type-params bracket into a function's original source, changing nothing else.

The function's formatting and comments are kept.
"""

import ast
import io
import re
import tokenize


def _name_end_offset(source: str, name: str) -> int:
    """Return the character offset right after `def name`/`async def name` in `source`.

    The `def` line may be indented, e.g. in a decorated function's source.
    """
    match = re.search(rf"^[ \t]*(async\s+)?def\s+{re.escape(name)}\b", source, re.MULTILINE)
    if match is None:
        message = f"no 'def {name}' header found"
        raise ValueError(message)
    return match.end()


def _bracket_end_offset(source: str, open_offset: int) -> int:
    """Return the offset right after the `]` matching the `[` at `open_offset` in `source`.

    Tracks bracket depth, so a nested `list[int]` doesn't close it early. A `[` or `]` inside a string
    literal is not accounted for.
    """
    depth = 0
    for offset in range(open_offset, len(source)):
        if source[offset] == "[":
            depth += 1
        elif source[offset] == "]":
            depth -= 1
            if depth == 0:
                return offset + 1
    message = "no closing ']' found"
    raise ValueError(message)


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
    message = "no header-terminating ':' found"
    raise ValueError(message)


def unparse_signature_only(node: ast.FunctionDef | ast.AsyncFunctionDef, original_text: str) -> str:
    """Insert node's PEP 695 type-params bracket into `original_text`, changing nothing else.

    `original_text` is node's source from before `node.type_params` was changed. An existing bracket
    after the function name (`def f[U](...)`) is replaced by the new one, which already holds both the
    old and new type parameters; otherwise a bracket is inserted.

    Everything else is kept, but lines after the first are re-indented relative to a column-0 `def`
    (see `_renormalize_indent`), since the rewriter adds the target's own indentation to them again.
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
    """Shift `lines` so their common leading indent becomes `target_indent`."""
    non_blank = [line for line in lines if line.strip()]
    if not non_blank:
        return lines
    # TODO: this minimum also counts lines inside multi-line string literals, which can change a literal's value.
    common = min(len(line) - len(line.lstrip(" ")) for line in non_blank)
    shift = common - target_indent
    if shift > 0:
        return [line[shift:] if line.strip() else line for line in lines]
    if shift < 0:
        pad = " " * -shift
        return [pad + line if line.strip() else line for line in lines]
    return lines

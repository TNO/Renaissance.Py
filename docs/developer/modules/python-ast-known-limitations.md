# Python AST known limitations

{ #codemod-python-ast-known-limitations }

**Stable ID:** `CODEMOD-PYTHON_AST_KNOWN_LIMITATIONS`

Concrete limitations found in the Python AST/RST layer (`renaissance.impl.python`) and the rewrite mechanism it
feeds (`renaissance.syntax_tree.ast_rewriter`, `renaissance.utils.text_utils`) while building recipes
(`TypeVarCheck`, `TypeVarTupleCheck`). None of these are patched here; they are documented so a recipe author knows
what to work around, and so a maintainer has a starting list for a proper fix.

## 1. `referenced_by` / `references` miss `self` and return annotations

`create_references` (`renaissance/impl/python/rst_node.py`) explicitly excludes parameters named `self`, and never
tracks a function's return-type annotation at all. A recipe that needs to know where a `self`-typed parameter or a
return annotation is used cannot rely on this reference tracking; it has to walk the tree directly instead.

## 2. `get_ancestor()` is declared but not available on `PythonRstNode`

`get_ancestor` is declared on the abstract `ASTNode` class, but the concrete Python class `PythonRstNode` does not
actually inherit from `ASTNode`, despite the structural similarity. Calling `get_ancestor` on a `PythonRstNode`
instance raises `AttributeError` at runtime. A recipe needing ancestor lookups has to write its own walk using
`.parent` and `.ast_type`, which are real attributes on `PythonRstNode`.

## 3. Unmapped `KIND_MAP` node types fail silently

`KIND_MAP` (`renaissance/impl/types.py`, over 2000 entries shared across every parser the framework supports) maps
every raw `ast` node type name to Renaissance's own `Type` class hierarchy. Two concrete gaps here -
`ast.Or` (the `or` operator) and `ast.MatMult` (the `@` operator) - have been fixed (both are now mapped, `Or` to
the `Or` class that already existed but was never wired in, `MatMult` to a new `MatrixMultiply` class), but the
underlying mechanism that let them go unnoticed is still there for any future unmapped node type.

When `PythonRstNode.__init__` (`renaissance/impl/python/rst_node.py`) meets an unmapped node type, it prints a debug
line intended to help someone add the missing entry, then carries on processing the node's children anyway. If that
then hits an `AttributeError`, the error is caught, printed, and **the node is silently dropped from the tree**
rather than raised or logged as a real failure.

**Consequence:** a future unmapped node type can leave parts of a file's AST missing, with no clear signal that this
happened beyond a printed line easy to miss in a large batch run. A recipe scanning for a pattern that happens to
sit inside an unmapped construct will silently miss it: a false negative, not a crash.

## 4. `shift_right`/`shift_left` double-indent docstrings after a rewrite

`TextUtils.shift_right`/`shift_left` (`renaissance/utils/text_utils.py`) are pure text operations with no notion of
Python syntax - they shift every line in a range unconditionally, blind to whether a line sits inside a string
literal. `renaissance/syntax_tree/ast_rewriter.py` calls them at three sites: `replace()`, `insert_before()`/
`insert_after()`, and `__get_texts()`'s mirror-image `shift_left` (under-dedenting instead of over-indenting).
`ast.unparse()` only ever emits a *docstring* as a real multi-line literal - every other multi-line string constant
gets collapsed to one line with `\n` escapes - and already reproduces a docstring's continuation lines verbatim, so
a whole-function/class/module replacement built from `ast.unparse()` then shifts those already-correctly-indented
lines a second time: one indentation level too many, and a genuinely blank line gains trailing whitespace. Confirmed
live against `sqlalchemy/lib/sqlalchemy/sql/elements.py` (the `cast` method); the same holds for class-level
docstrings, while single-line docstrings are unaffected (no embedded newline to double-shift).

**Consequence:** not a correctness bug - indentation inside a string literal has no syntactic meaning - but an
unwanted formatting diff to the docstring's internal whitespace on any whole-function/class/module rewrite built
from `ast.unparse()`. Today only `TypeVarCheck.convert_declared_typevars` triggers it, being the only recipe that
replaces a whole function this way, but it's a shared rewrite-mechanism gap, not something specific to `TypeVarCheck`.

**Worked around in `TypeVarCheck` (not fixed in the shared mechanism).** Before `ast.unparse()` runs,
`type_var_check.py`'s `_normalize_docstring_indent` rewrites a docstring's continuation lines to one canonical
indent, preserving each line's indentation *relative* to that baseline so nested content (e.g. a Sphinx
`.. seealso::` block) stays nested, leaving nothing pre-existing for the later shift to double up on. Verified line
for line against the same real file, with one residual cosmetic-only difference (blank lines gain trailing
whitespace).
Any future recipe replacing/inserting a docstring-containing function/class/module the same way would need the same
kind of workaround, absent a proper fix in `ast_rewriter.py`/`text_utils.py` themselves. A related but distinct side
effect - whole-function replacement reformatting the entire body, not just the changed signature - is a
`TypeVarCheck` design trade-off tracked separately in
[TypeVar modernization](../../user/features/typevar-modernization.md)'s Change considerations, not a framework bug.

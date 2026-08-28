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
then hits an `AttributeError` - as it does for the `None`-in-a-list case in item 4 below - the error is caught,
printed, and **the node is silently dropped from the tree** rather than raised or logged as a real failure.

**Consequence:** a future unmapped node type can leave parts of a file's AST missing, with no clear signal that this
happened beyond a printed line easy to miss in a large batch run. A recipe scanning for a pattern that happens to
sit inside an unmapped construct will silently miss it: a false negative, not a crash.

## 4. A bare `None` inside an AST list field crashes RstNode construction

Some `ast` list fields can contain a literal `None` as one of their elements, not just `ast.AST` nodes. Confirmed
live against a real file (`sqlalchemy/lib/sqlalchemy/sql/elements.py`): `ast.arguments.kw_defaults` holds one entry
per keyword-only argument, and a keyword-only argument with no default gets `None` at its position (e.g.
`def f(self, *, column_keys: List[str], schema_translate_map=None): ...` - `column_keys` has no default, so its
`kw_defaults` slot is `None`; `schema_translate_map`'s slot holds the `Constant(None)` default expression instead,
which is a real node, not the same thing). The same `None`-marks-absence pattern also exists elsewhere in the `ast`
module - for example `ast.Dict.keys` puts `None` at the position of a `**other` merge in a dict literal - so this
is one instance of a more general shape, not a one-off.

`PythonRstNode.__init__`'s list-expansion path (`renaissance/impl/python/rst_node.py`, around line 224) does not
guard against a `None` element when expanding such a list into child nodes; it constructs `PythonRstNode(None, ...)`
directly. That trips the same unmapped-type path as item 3 above (`type(None).__name__` is `"NoneType"`, and no
such key belongs in `KIND_MAP` - `None` isn't a real AST node type at all), then crashes on the very next line
(`for name in node._fields:`) with `AttributeError: 'NoneType' object has no attribute '_fields'`, caught and
silently dropped the same way.

**Consequence:** any function signature with a keyword-only argument that has no default (a common, ordinary
pattern - confirmed 12 occurrences in this one real file) silently loses part of its AST. A recipe inspecting
function signatures or argument defaults in code using this pattern will get an incomplete tree with no error
raised.

## 5. `shift_right`/`shift_left` double-indent docstrings after a rewrite

Confirmed live by running `TypeVarCheck` against a real file (`sqlalchemy/lib/sqlalchemy/sql/elements.py`, a method
called `cast` with a multi-line docstring), then isolated with a minimal reproduction.

**Scope is narrower than it first looked - docstrings specifically, not multi-line strings in general.** Tested
directly: `ast.unparse()` only ever emits a string as an actual multi-line, newline-containing literal when that
string is a *docstring* (the leading bare-string-expression statement of a function/class/module body) - Python's
unparser special-cases exactly that position. Every other multi-line string constant (e.g. a query string assigned
to a variable mid-function) gets collapsed by `ast.unparse()` into a single text line with `\n` written as a
literal escape sequence (confirmed: `query = '\n        SELECT *\n...'`, one line, no embedded newlines). A
per-line shift can only double-indent content that actually spans multiple *text* lines in the first place, so
only the docstring case is at risk.

`TextUtils.shift_right`/`shift_left` (`renaissance/utils/text_utils.py`) are pure text operations with no notion of
Python syntax: `shift_right` prepends `shift` spaces to every line of the input from `start_line` onward,
unconditionally; `shift_left` strips up to `shift` leading spaces the same way. Neither knows some of those lines
might sit inside a string literal rather than being independent statements. Four call sites share this flaw, all
in `renaissance/syntax_tree/ast_rewriter.py`:

- `shift_right(new_content, indent, start_line=1)` in the `replace()` path (line 286).
- The same call in the `insert_before()`/`insert_after()` path (line 362).
- `shift_left(result, indent, start_line=1)` in `__get_texts()` (line 431), used when extracting matched text that
  spans multiple nodes for pattern-matching-based rewrites - the mirror-image bug (under-dedenting instead of
  over-indenting).

For a docstring specifically, since `ast.unparse()` already reproduces its continuation lines' original
indentation verbatim (confirmed: unparsing a function with an 8-space-indented docstring continuation line
reproduces exactly 8 spaces, unchanged - `ast.unparse` does not re-indent docstrings on its own), the extra shift
lands on top of already-correct content:

- A docstring continuation line that already carried its own correct indentation (verbatim from the original
  source) gets a further, unwanted shift added on top - one indentation level too many.
- A line that was genuinely blank inside the docstring gains trailing whitespace equal to the shift amount,
  instead of staying empty.

**Further verified:**

- **Not function-specific.** A *class*-level docstring is affected identically - tested unparsing and shifting a
  `ClassDef` with a multi-line docstring, same double-indent result. Any future whole-class or whole-module
  replacement would carry the same risk, not just `TypeVarCheck`'s whole-function one.
- **Single-line docstrings are safe.** Tested directly: a one-line docstring (`"""One liner."""`) shifts correctly
  with no double-indentation - there's no embedded newline for a per-line shift to double-apply to, so only
  docstrings spanning 2+ physical lines are at risk.
- **No existing test would have caught this.** None of `test_type_var_check.py`'s fixtures for
  `convert_declared_typevars`/`check`/`run` give the converted function a docstring at all (checked: zero matches
  for a docstring immediately following a `def` line in any fixture) - this bug was invisible to the test suite by
  construction, only surfacing once a real file was tried.

**Blast radius today:** only `TypeVarCheck.convert_declared_typevars` triggers this in practice, since it's the
only recipe that calls `self.replace(ast.unparse(function), ...)` with a whole function body (confirmed: no other
file under `src/renaissance/refactoring/` calls `ast.unparse`). Any future recipe that replaces or inserts a
function/class/module with a docstring the same way would hit it too - this is a shared rewrite-mechanism gap, not
something specific to `TypeVarCheck`.

**Consequence:** not a correctness bug - the file stays valid Python, since indentation inside a string literal's
content has no syntactic meaning - but an unwanted formatting diff to the docstring's internal whitespace that a
real maintainer reviewing the change would notice.

**Worked around in `TypeVarCheck` (not fixed in the shared mechanism).** Rather than touching `ast_rewriter.py` or
`text_utils.py` - shared, language-agnostic code used by every recipe and every parser backend, not just Python -
`type_var_check.py` neutralizes the problem entirely on the input side: `_normalize_docstring_indent` rewrites a
multi-line docstring's continuation lines to a single canonical indent (matching the indent `ast.unparse()` already
gives any function-body statement) *before* `_unparse_function` calls `ast.unparse()`, while preserving each line's
indentation *relative* to that canonical level (so an internally-nested block, e.g. a Sphinx `.. seealso::` list,
keeps its own extra indentation rather than being flattened). With nothing pre-existing left for the later uniform
shift to double up on, the shift lands each line at the correct depth on the first pass. Verified against the same
real file that surfaced the bug (`sqlalchemy/lib/sqlalchemy/sql/elements.py`, the `cast` method, including its
nested `.. seealso::` block) - the docstring's content now matches the original exactly, line for line. The one
residual, purely cosmetic difference: a line that was genuinely blank inside the docstring still gains trailing
whitespace equal to the shift amount (unavoidable without also touching the shared shift mechanism - not worth the
added risk for a difference invisible to a reader and irrelevant to Python's syntax).

This workaround only covers `TypeVarCheck`'s own whole-function replacement. The underlying flaw in
`shift_right`/`shift_left` themselves is unchanged and would still bite any future recipe that replaces or inserts
a docstring-containing function/class/module the same way, unless it adopts the same kind of workaround (or the
shared mechanism gets a proper, language-agnostic fix - see the blast-radius note above).

A related but distinct side effect - whole-function replacement reformatting the entire body, not just the
signature that actually changed - is a `TypeVarCheck`-specific design trade-off rather than a framework bug, so
it's tracked in the feature's own docs instead: see the Change considerations section of
[TypeVar modernization](../../user/features/typevar-modernization.md).

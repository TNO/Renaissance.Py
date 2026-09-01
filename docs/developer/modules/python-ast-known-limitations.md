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

## 4. `ast.unparse()`/`shift_right` lose comments and indentation

`TextUtils.shift_right`/`shift_left` (`renaissance/utils/text_utils.py`) are pure text operations with no notion of
Python syntax - they shift every line in a range unconditionally, blind to whether a line sits inside a string
literal. `ast.unparse()` already reproduces a docstring's continuation lines verbatim (it's the only multi-line
string constant it emits as a real multi-line literal), so a whole-function/class/module replacement built from
it shifts those already-correctly-indented lines a second time. Separately, regenerating a function's entire body
from the AST also reformats it to `ast.unparse()`'s own style regardless of the original formatting, and -
permanently, since Python's `ast` module never records comments at all - **deletes every comment inside the
body**; there is nothing for `ast.unparse()` to reproduce, and no future fix to this framework can change that
without Python itself changing. Both are real for any recipe that regenerates a whole node's source via
`ast.unparse()` and replaces the original text with it wholesale.

**`TypeVarCheck` avoids this, it doesn't fix it.** `renaissance.utils.unparse_utils.unparse_signature_only`
replaces only a function's signature line(s), never the body: it `ast.unparse()`s the whole (mutated) node to get
a correctly-formatted new header, finds where that header ends (via `tokenize`, tracking bracket depth so a colon
inside a string default, a lambda default, or an annotation isn't mistaken for the real one), and splices it onto
the *original* body text - comments, docstring formatting, and everything else untouched byte-for-byte, since
that text is never passed through `ast.unparse()` or `shift_right` at all. `TypeVarCheck.convert_declared_typevars`
uses it in place of the old `unparse_node`/`normalize_docstring_indent` pair, which are retired. Verified against
a method's body (whose `.text` carries the file's real absolute indentation rather than the 4-space-relative-to-
zero baseline `ast.unparse()`/the rewrite pipeline's shift expect - renormalized before splicing), an inline
single-line body (`def f(x): ...`, kept inline rather than forced onto its own line), and the `starlette` case
that surfaced this (see [Refactoring recipes](../../developer/modules/recipes.md)).

A future recipe that genuinely needs to regenerate a whole body from the AST - not just a signature - still hits
both issues above and has to work around them itself; neither `ast.unparse()`'s comment blindness nor
`shift_right`/`shift_left`'s string-literal blindness was touched here.

## 5. Overlapping rewrites in one batch corrupt output instead of merging

`_RewriteActions.__is_ancestor_in_nodes` (`renaissance/syntax_tree/ast_rewriter.py`) is meant to detect when two
pending edits target overlapping source ranges, so `apply()` can skip the redundant one - but it ends with
`return result and False`, which is always `False` regardless of `result`. The overlap check never fires. Two
`replace()`/`remove()` calls queued against the same (or overlapping) node before the next `commit()` both get
applied back to back, with no merging, ordering, or error - just concatenated/garbled text.

**Consequence (before the fix below):** any recipe or base-class helper that edits the same node - e.g. the same
`from ... import ...` statement, or the same function - more than once within one uncommitted batch produced
invalid output instead of a clean result or a clear failure. Confirmed live in two places: `TypeVarCheck.
convert_declared_typevars`, run against a file with `from typing import ParamSpec, TypeVar` where both names get
converted in the same pass, called `PythonRefactoring.remove_import_alias()` twice against that same import
statement, producing `from typing import TypeVarfrom typing import ParamSpec`; and the same recipe, run against a
function using two different type params, replacing that function twice, producing its body duplicated back to
back. Both are `SyntaxError` on the next parse.

**Fixed: `apply()` now raises instead of corrupting.** `_RewriteActions.apply()` calls a new
`__check_for_conflicting_rewrites()` that detects two queued rewrites on overlapping source ranges (excluding
genuine ancestor/descendant nesting, walked via `.parent` rather than `.is_ancestor_of()` since not every
`Rewritable` implements it - e.g. `PythonRstNode`) and raises `ValueError` instead of applying both. This matches
the pre-existing "Error cases" group already specified in `features/rewrite-semantics.feature` and its Hypothesis
counterpart `test_replacing_same_node_twice_always_errors` (`test/syntax_tree/test_rewrite_semantics_properties.py`),
previously `xfail(strict=True)` and now passing, so the marker was removed. This only turns silent corruption into
a clear error; it does not merge conflicting rewrites into a correct result, so callers must still avoid queuing
more than one rewrite per node/range before a commit.

**Still broken, not touched by the fix above:** the same feature file's "Dominance and suppression" group (an
ancestor replacement should silently suppress a nested descendant edit, not error and not apply both) is a
separate, pre-existing gap - confirmed live that a queued descendant edit still leaks into the output instead of
being suppressed. `__is_ancestor_in_nodes` itself (the `return result and False` line) is untouched.

Confirmed live a second time, and with a previously-undocumented mechanical detail: `renaissance/common/rewriter.py`'s
low-level `Rewriter.replace()` doesn't reject or merge an edit whose `start` offset falls inside an
*already-queued* edit's range - it just appends the new edit's replacement bytes onto the end of the existing one
(`r.replacement += new_content`), with no separator. So when a nested edit isn't suppressed, its text doesn't
overwrite or nest cleanly inside the ancestor edit's output - it gets tacked directly onto the end of it, producing
concatenated/garbled text (e.g. `return decoratorapper@functools.wraps(func)`). This was hit for real via a
`TypeVarCheck` domain bug (`functions_using_nodes` wrongly attributing a type parameter's usage to a nested
closure instead of its outermost owning function, queuing a redundant nested edit) - that domain bug is now fixed
(see [Refactoring recipes](../../developer/modules/recipes.md)), so this dominance/suppression gap and the
`Rewriter.replace()` wrinkle are no longer reachable through `TypeVarCheck`, but remain open for any future recipe
that queues genuinely nested edits.

**Workarounds applied in `TypeVarCheck`/`PythonRefactoring` (both `# TODO`-marked, pointing back here):**
`PythonRefactoring.remove_import_alias()` now accepts a set of names and narrows/removes each shared import in one
edit instead of one call per name; `TypeVarCheck.convert_declared_typevars` collects every function touched by
any converted type param and does exactly one `unparse_signature_only()`+`replace()` per function (see item 4),
after the whole pass, instead of one per name. Neither ever queues a second rewrite on the same node, so neither
ever reaches the new check.

**Other, unrelated occurrences found once the check went live**, all previously passing on silently corrupted
output that happened to still satisfy their assertion, now correctly rejected - none fixed here, out of scope for
this session's work on `TypeVarCheck`:

- `Taut2Pyunit.convert_setup()` and `insert_asserter()`/`remove_assert_func()`
  (`renaissance/refactoring/taut2pyunit.py`). Tests `test_setup`, `test_insert_asserter`
  (`test/refactoring/test_taut2unittest_refactoring.py`) marked `xfail(strict=True)`.
- `example_add_comment_and_commit` and `remove_unused_variable_using_refactor_method`
  (`src/rejuvenation/refactor_examples_different_styles.py` and its neighbouring example module) - demo/example
  code shipped with the framework, not a recipe. Six affected test variants in
  `test/examples/test_examples.py` marked `xfail` (two of them conditionally, via `pytest.xfail()` inside the
  test body, since only some of their parametrizations are affected).

## 6. `Global`/`Nonlocal`'s `names` list crashes the tree builder (silently swallowed)

`PythonRstNode.__init__` (`renaissance/impl/python/rst_node.py:212-232`) assumes any AST node whose `_fields`
tuple has exactly one entry, and whose value there is a list, holds a list of *child AST nodes* - that branch
recurses into `PythonRstNode(n, translation_unit, self)` for each list element. `ast.Global`/`ast.Nonlocal` don't
fit that assumption: their sole field (`names`) is `list[str]` - plain Python strings, not AST nodes. Constructing
a `PythonRstNode` from a bare string crashes immediately (`node._fields` on a `str`), since that access sits at
the very top of `__init__`, outside any try/except.

**Consequence:** the crash *is* caught, one level up, by the broad `except AttributeError as e: print(e);
continue` already wrapping this loop (there to catch other, unrelated per-field failures) - so parsing a file
with a `global`/`nonlocal` statement doesn't hard-fail; it prints `'str' object has no attribute '_fields'` (once
per name-list) and moves on. But that means the `Global`/`Nonlocal` node's name list never becomes RST children at
all - silently dropped, similar in spirit to item 3's silent-drop behaviour but a different mechanism (a genuine
construction bug, not an unmapped `KIND_MAP` entry). Confirmed live parsing `starlette/starlette/testclient.py`,
which has two `nonlocal` statements - one printed warning per statement, tree still builds and the recipe
otherwise completes normally.

Not fixed here - found via a `TypeVarCheck` run whose target file happened to contain `nonlocal`, but the bug
itself lives entirely in the generic parsing layer (`rst_node.py`), unrelated to any recipe.

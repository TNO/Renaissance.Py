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

**Available as a shared workaround (not fixed in `ast_rewriter.py`/`text_utils.py` themselves).** Before
`ast.unparse()` runs, `renaissance.utils.unparse_utils.normalize_docstring_indent` rewrites a docstring's
continuation lines to one canonical indent, preserving each line's indentation *relative* to that baseline so
nested content (e.g. a Sphinx `.. seealso::` block) stays nested, leaving nothing pre-existing for the later shift
to double up on. `TypeVarCheck.convert_declared_typevars` uses it via that module's `unparse_node`, so any future
recipe replacing/inserting a docstring-containing function/class/module the same way can reuse it directly instead
of reimplementing the workaround, absent a proper fix in `ast_rewriter.py`/`text_utils.py` themselves. Verified
line for line against the real file that surfaced the bug, with one residual cosmetic-only difference (blank
lines gain trailing whitespace). A related but distinct side
effect - whole-function replacement reformatting the entire body, not just the changed signature - is a
`TypeVarCheck` design trade-off tracked separately in
[TypeVar modernization](../../user/features/typevar-modernization.md)'s Change considerations, not a framework
bug. That item's future fix (replacing only the signature, leaving the body's original bytes untouched) would
retire this workaround too, as a bonus rather than something to fix separately - the docstring would never be
regenerated via `ast.unparse()` at all.

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

**Workarounds applied in `TypeVarCheck`/`PythonRefactoring` (both `# TODO`-marked, pointing back here):**
`PythonRefactoring.remove_import_alias()` now accepts a set of names and narrows/removes each shared import in one
edit instead of one call per name; `TypeVarCheck.convert_declared_typevars` collects every function touched by
any converted type param and does exactly one `unparse()`+`replace()` per function, after the whole pass, instead
of one per name. Neither ever queues a second rewrite on the same node, so neither ever reaches the new check.

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

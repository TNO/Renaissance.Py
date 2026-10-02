# Python AST known limitations

{ #codemod-python-ast-known-limitations }

**Stable ID:** `CODEMOD-PYTHON_AST_KNOWN_LIMITATIONS`

Concrete limitations found in the Python AST/RST layer (`renaissance.integrations.python.ast`) and the rewrite mechanism it
feeds (`renaissance.syntax_tree.ast_rewriter`, `renaissance.utils.text_utils`) while building recipes
(`TypeVarCheck`, `TypeVarTupleCheck`). A recipe still has to work around both items below. Item 1 has no other
tracker in the codebase. Item 2 is also tracked by a `# TODO` at the `return` in `ast_rewriter.py`, by `xfail`
scenarios in `features/steps/test_rewrite_semantics.py` and `test/syntax_tree/test_ast_rewriter.py`, and by tests
skipped with `TODO: fix impl.` in the latter; this page records why the obvious fix does not work.

## 1. `ast.unparse()`/`shift_right` lose comments and indentation

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

**`TypeVarCheck` avoids this, it doesn't fix it** - see [Refactoring recipes](../../developer/modules/recipes.md)
for how `unparse_signature_only` splices only the new `[T]`/`[**P]`/`[*Ts]` bracket into the function's original
text instead of regenerating anything via `ast.unparse()`.

The avoidance is not complete. `unparse_signature_only` still re-indents the function's lines (`_renormalize_indent`),
taking the *smallest* indentation among the body's non-blank lines as the body's own indentation, and that is
blind to string literals too. A multi-line string literal in the body with a continuation line indented less than
the body (for example at column 0) lowers that minimum: the function is re-indented from the wrong baseline and
the literal's contents change silently (`'first\nsecond'` becomes `'first\n    second'`). This reproduces with
`TypeVarCheck.convert_declared_typevars` on both a module-level function and a method; a literal whose
continuation lines are indented like the body is not affected.

A future recipe that genuinely needs to regenerate a whole body from the AST - not just a signature - still hits
both issues above and has to work around them itself; neither `ast.unparse()`'s comment blindness nor
`shift_right`/`shift_left`'s string-literal blindness was touched here.

## 2. `__is_ancestor_in_nodes` can't just drop its `and False`

`_RewriteActions.__is_ancestor_in_nodes` (`renaissance/syntax_tree/ast_rewriter.py`) is meant to detect when a
queued rewrite is nested inside another queued rewrite's node, so `apply()` can skip the redundant nested one and
let the outer (ancestor) rewrite silently dominate it - but it ends with `return result and False`, which is
always `False` regardless of `result`. The dominance/suppression check never fires: an ancestor replacement and a
nested descendant edit queued in the same batch both get applied instead of the descendant being suppressed. The
one-line in-code `# TODO` at that `return` doesn't capture why this isn't a one-line fix, so it's spelled out here
instead.

**Why the obvious one-line fix doesn't work:** simply changing `return result and False` to `return result`
does not enable the suppression correctly. `no_conflict(node, rew)` returns `True` for `node is rew` (a node
trivially "overlaps" itself), and `rewrite_nodes` is built by flattening every rewrite in `self.rewrites` - the
same collection `apply()` draws `n` from when it calls `__is_ancestor_in_nodes(n)`. So `result` is a near-total
tautology: `True` for almost any node, since it always includes a self-comparison. Dropping `and False` would
make `__is_ancestor_in_nodes` return `True` for nearly every queued node - including nodes that have no real
ancestor/descendant relationship to anything else - so `apply()`'s `continue` would skip most rewrites, not
just the dominated ones, breaking the majority of currently-passing scenarios rather than fixing the dominance
scenarios that are marked `xfail` (for example `test_dominated_change_not_applied` in
`features/steps/test_rewrite_semantics.py`). A real fix needs to exclude a node's own rewrite from the comparison set and use a genuine
ancestor/descendant check - e.g. reusing `__is_nested` (already used by `__check_for_conflicting_rewrites`, the
sibling check that turns a *different* kind of overlapping-rewrite bug into a clear `ValueError` instead of
corrupting output) - instead of repairing `no_conflict`'s offset-overlap test.

`TypeVarCheck` avoids triggering this gap by construction: `functions_using_nodes` attributes a name to the
outermost function using it, so a nested closure never gets an edit of its own alongside its parent's. See
[Refactoring recipes](recipes.md), which also describes how `convert_declared_typevars` queues exactly one edit per
function, never a second rewrite on the same node.

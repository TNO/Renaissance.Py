# Python AST known limitations

{ #codemod-python-ast-known-limitations }

**Stable ID:** `CODEMOD-PYTHON_AST_KNOWN_LIMITATIONS`

Concrete limitations found in the Python AST/RST layer (`renaissance.integrations.python.ast`) and the rewrite mechanism it
feeds (`renaissance.syntax_tree.ast_rewriter`, `renaissance.utils.text_utils`) while building recipes
(`TypeVarCheck`, `TypeVarTupleCheck`). Most of these are not patched here - a recipe has to work around them, and
a maintainer has a starting list for a proper fix - except where a fix is noted below.

## 1. `referenced_by` / `references` miss `self` and return annotations

`create_references` (`renaissance/integrations/python/ast/rst_node.py`) explicitly excludes parameters named `self`, and never
tracks a function's return-type annotation at all. A recipe that needs to know where a `self`-typed parameter or a
return annotation is used cannot rely on this reference tracking; it has to walk the tree directly instead.

## 2. `get_ancestor()` is declared but not available on `PythonRstNode`

`get_ancestor` is declared on the abstract `ASTNode` class, but the concrete Python class `PythonRstNode` does not
actually inherit from `ASTNode`, despite the structural similarity. Calling `get_ancestor` on a `PythonRstNode`
instance raises `AttributeError` at runtime. A recipe needing ancestor lookups has to write its own walk using
`.parent` and `.parser_kind`, which are real attributes on `PythonRstNode`.

## 3. Unmapped `PYTHON_KIND_MAP` node types degrade to a generic kind

`PYTHON_KIND_MAP` (`renaissance/integrations/python/ast/kinds.py`, ~48 entries, Python-specific - every parser
integration now keeps its own `kinds.py`) maps a raw `ast` node type's class name to a `SemanticKind` enum member.
`PythonRstNode.__init__` (`renaissance/integrations/python/ast/rst_node.py`) looks this up with
`PYTHON_KIND_MAP.get(self.parser_kind, SemanticKind.NODE)`: a node type absent from the map simply becomes generic
`SemanticKind.NODE` - no debug print, no exception, and the node is still built and kept in the tree. `ast.Or`
(the `or` operator) and `ast.MatMult` (the `@` operator) are two concrete examples currently unmapped.

**Consequence:** a recipe that matches nodes by exact `semantic_kind` (e.g. looking for a specific operator kind)
will simply never match an unmapped node type - it falls through as generic `SemanticKind.NODE` instead, with no
error. This is a false negative in matching, not a missing node in the tree: the node itself is present and
traversable, just under a less specific kind than expected. Matching on `.parser_kind` directly (the raw `ast`
class name, e.g. `"BoolOp"`) or on `isinstance(node.node, ast.Or)` sidesteps this entirely.

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

**`TypeVarCheck` avoids this, it doesn't fix it** - see [Refactoring recipes](../../developer/modules/recipes.md)
for how `unparse_signature_only` splices only the new `[T]`/`[**P]`/`[*Ts]` bracket into the function's original
text instead of regenerating anything via `ast.unparse()`.

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
invalid output instead of a clean result or a clear failure: two edits against one import statement can produce
`from typing import TypeVarfrom typing import ParamSpec`, and a function replaced twice can end up with its body
duplicated back to back. Both are `SyntaxError` on the next parse.

Underlying mechanism: `renaissance/common/rewriter.py`'s low-level `Rewriter.replace()` doesn't reject or merge an
edit whose `start` offset falls inside an already-queued edit's range - it appends the new edit's replacement
bytes onto the end of the existing one (`r.replacement += new_content`), with no separator, which is why the
result is concatenated/garbled rather than merged or overwritten.

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
separate, pre-existing gap - a queued descendant edit still leaks into the output instead of being suppressed.
`__is_ancestor_in_nodes` itself (the `return result and False` line) is untouched.

`TypeVarCheck` avoids triggering either gap by construction - see [Refactoring recipes](../../developer/modules/recipes.md)
for how `convert_declared_typevars` collects every touched function and queues exactly one edit per node, never a
second rewrite on the same node.

**Tests marked `xfail` because they used to pass on silently corrupted output** that happened to still satisfy
their assertion, now correctly rejected by the fix above:

- `Taut2Pyunit.convert_setup()` and `insert_asserter()`/`remove_assert_func()`
  (`renaissance/refactoring/taut2pyunit.py`): `test_setup`, `test_insert_asserter`
  (`test/refactoring/test_taut2unittest_refactoring.py`), `xfail(strict=True)`.
- `example_add_comment_and_commit` and `remove_unused_variable_using_refactor_method`
  (`src/rejuvenation/refactor_examples_different_styles.py` and its neighbouring example module) - demo/example
  code shipped with the framework, not a recipe: six variants in `test/examples/test_examples.py`, `xfail`.
- `CleanupRefactoring.remove_unused_variables` (`src/renaissance/recipes/cleanup_refactoring.py`): a
  `VariableDef` nested inside a block is discovered twice - once via its own enclosing `CompoundStatement`'s
  recursive scan, once via every ancestor `CompoundStatement`'s scan - so a shadowed unused variable (e.g.
  `int unused = 0;` declared in both a function body and a nested `if` block) gets queued for removal twice.
  Exercised via `batch_remove_unused_variable_once_example`/`batch_repeat_example`
  (`src/rejuvenation/batch_process_examples.py`): `test_make_sure_that_batch_remove_proc_still_run`,
  `test_make_sure_that_batch_repeat_proc_still_run` (`test/examples/test_examples.py`), `xfail(strict=True)`.

## 6. `Global`/`Nonlocal`'s `names` list crashes the tree builder (silently swallowed)

`PythonRstNode.__init__` (`renaissance/integrations/python/ast/rst_node.py:208-222`) assumes any AST node whose `_fields`
tuple has exactly one entry, and whose value there is a list, holds a list of *child AST nodes* - that branch
recurses into `PythonRstNode(n, translation_unit, self)` for each list element. `ast.Global`/`ast.Nonlocal` don't
fit that assumption: their sole field (`names`) is `list[str]` - plain Python strings, not AST nodes. Constructing
a `PythonRstNode` from a bare string crashes immediately (`node._fields` on a `str`), since that access sits at
the very top of `__init__`, outside any try/except.

**Consequence:** the crash *is* caught, one level up, by the broad `except AttributeError as e: print(e);
continue` already wrapping this loop (there to catch other, unrelated per-field failures) - so parsing a file
with a `global`/`nonlocal` statement doesn't hard-fail; it prints `'str' object has no attribute '_fields'` (once
per name-list) and moves on. But that means the `Global`/`Nonlocal` node's name list never becomes RST children at
all - silently dropped. This is a genuine construction bug, unrelated to item 3's generic-kind fallback for
unmapped `PYTHON_KIND_MAP` entries (that one keeps the node, just under a less specific kind; this one loses the
node entirely). Confirmed live parsing `starlette/starlette/testclient.py`,
which has two `nonlocal` statements - one printed warning per statement, tree still builds and the recipe
otherwise completes normally.

Not fixed here - found via a `TypeVarCheck` run whose target file happened to contain `nonlocal`, but the bug
itself lives entirely in the generic parsing layer (`rst_node.py`), unrelated to any recipe.

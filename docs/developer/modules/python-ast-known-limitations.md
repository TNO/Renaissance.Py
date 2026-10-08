# Python AST known limitations

{ #codemod-python-ast-known-limitations }

**Stable ID:** `CODEMOD-PYTHON_AST_KNOWN_LIMITATIONS`

Two limitations of the Python AST layer and the rewriter that any recipe has to work around. `TypeVarCheck` avoids
both; see [Refactoring recipes](recipes.md).

## 1. `ast.unparse()` and `shift_right` lose comments and indentation

Replacing a whole node with `ast.unparse()` output has two problems:

- `ast` never records comments, so every comment inside the node is **deleted**, and the code is reformatted.
- `TextUtils.shift_right`/`shift_left` (`renaissance/utils/text_utils.py`) shift every line, also inside string
  literals, so a docstring's continuation lines are indented twice.

`TypeVarCheck` avoids this with `unparse_signature_only`, which only inserts the type-parameter bracket into the
original text. It still re-indents the function from the smallest indentation in the body (`_renormalize_indent`),
so a multi-line string literal with a line indented less than the body has its contents changed. Tracked by the
`xfail` test `test_converts_function_preserving_multiline_string_literal` in
`test/recipes/test_type_var_check_convert.py`.

## 2. `__is_ancestor_in_nodes` can't just drop its `and False`

`_RewriteActions.__is_ancestor_in_nodes` (`renaissance/syntax_tree/ast_rewriter.py`) should let an outer rewrite
suppress a rewrite nested inside it, but it ends with `return result and False`, so it never does: both are applied.

Removing `and False` is not enough. `no_conflict` also compares each node with its own rewrite, so `result` is
almost always `True` and `apply()` would skip nearly every rewrite. A real fix has to leave out the node's own
rewrite and use a true ancestor check such as `__is_nested`.

`TypeVarCheck` never queues a nested edit: each name goes to the outermost function only. Tracked by the `# TODO`
at that `return`, by `xfail` scenarios such as `test_dominated_change_not_applied` in
`features/steps/test_rewrite_semantics.py`, and by `xfail` and skipped (`TODO: fix impl.`) tests in
`test/syntax_tree/test_ast_rewriter.py`.

{ #codemod-python-ast-known-limitations }
# Python AST known limitations

**Stable ID:** `CODEMOD-PYTHON_AST_KNOWN_LIMITATIONS`

Concrete limitations found in the Python AST/RST layer (`renaissance.impl.python`) while building recipes (`TypeVarCheck`, `TypeVarTupleCheck`). None of these are patched here; they are documented so a recipe author knows what to work around, and so a maintainer has a starting list for a proper fix.

## 1. `referenced_by` / `references` miss `self` and return annotations

`create_references` (`renaissance/impl/python/rst_node.py`) explicitly excludes parameters named `self`, and never tracks a function's return-type annotation at all. A recipe that needs to know where a `self`-typed parameter or a return annotation is used cannot rely on this reference tracking; it has to walk the tree directly instead.

## 2. `get_ancestor()` is declared but not available on `PythonRstNode`

`get_ancestor` is declared on the abstract `ASTNode` class, but the concrete Python class `PythonRstNode` does not actually inherit from `ASTNode`, despite the structural similarity. Calling `get_ancestor` on a `PythonRstNode` instance raises `AttributeError` at runtime. A recipe needing ancestor lookups has to write its own walk using `.parent` and `.ast_type`, which are real attributes on `PythonRstNode`.

## 3. `KIND_MAP` is missing some Python operator nodes, and unmapped nodes fail silently

`KIND_MAP` (`renaissance/impl/types.py`, over 2000 entries shared across every parser the framework supports) has no entry for at least `ast.Or` (the `or` operator) and `ast.MatMult` (the `@` operator). `BoolOp` (the containing node for an `and`/`or` expression) *is* mapped; the operator inside it is not.

When `PythonRstNode.__init__` (`renaissance/impl/python/rst_node.py`) meets an unmapped node type, it prints a debug line intended to help someone add the missing entry, then carries on processing the node's children anyway. If that then hits an `AttributeError`, which it does for `Or`/`MatMult`, and for bare `None`/`str` values that turn up in some AST fields, the error is caught, printed, and **the node is silently dropped from the tree** rather than raised or logged as a real failure.

**Consequence:** code containing `@` or `or` (both common in numeric/scientific Python; confirmed against a real clone of `pytorch`) can end up with parts of its AST missing, with no clear signal that this happened. A recipe scanning for a pattern that happens to sit inside one of these unmapped constructs will silently miss it: a false negative, not a crash.

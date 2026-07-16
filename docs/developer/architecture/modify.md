{ #dev-architecture-code-modify }
# Modify

**Stable ID:** `ARCH-CODE-MODIFY`

## Purpose

Document the design decisions that determine how the modify step is implemented within the find-filter-modify workflow.

## Scope

The modify step transforms code at matched locations that have passed the [filter](filter.md) step.
It does not locate or filter matches — those are the responsibilities of the [find](find.md) and [filter](filter.md) steps.

## Definition

When a match is found, the modify step either replaces the entire match or performs targeted manipulation within it.

### Replace vs manipulate

**Replace** substitutes the entire matched node with new text or a new pattern.
**Manipulate** performs targeted modifications within the match, such as inserting text before a placeholder or replacing a placeholder within the match.

Code owners typically prefer minimally invasive changes: layout should be preserved and comments should not be removed.
Because whitespace and comments are ignored when building an AST, manipulation within the match produces smaller diffs that are easier for code owners to review and accept.

**Decision**

Both complete replacement of a match and manipulation within a match are supported.

### Replacement text vs pattern

Replacing with **text** enables unstructured replacement and migration to another programming language (transpilation).

Replacing with a **pattern** enables:

* enforcing correctness by checking that the find and replacement patterns share a base type;
* correctly handling syntax tokens, including separators, when placeholders are empty — for example:
  * the keyword `else` is absent when that branch has no statements;
  * in the function call `f($$before, 1)`, the comma is removed when `$$before` is empty.

**Decision**

At minimum, replacement by text is supported.

### AST-aware removal

When an AST node is removed, the resulting code may no longer be syntactically correct.
For example, removing the function call `f()` from:

```python
if cond:
    f()
```

results in invalid Python code.

Correctness of the final code is not guaranteed by text replacement.

**Decision**

The user is responsible for ensuring that removal of an AST node results in correct code.

For efficiency, it is recommended that the [standard libraries](standard-libraries.md#ast-aware-removal-of-node) provide, for each language, functionality for correct removal of an AST node in all situations.

### Meta data 

Analysis or a match (with a failing filter) do not justify that the the file or folder containing that source code changes.
This not only holds for the content, but also the meta-data of the file and folder.
A file and folder, including their meta-data, are only allowed to change when the contained source code changes.

#### Corner case - identity transformations

Should an identity transformation, like a node replaced by itself,  be considered a change?

The memory usage increases when the original content and the modified content have to be compared.

As file access is slow, preventing unnecessary file access will improve execution performance.

Scarce resources are needed to develop and maintain the logic to check for real, non-trivial changes.

A transformation can always be designed, e.g., by including an equality check, to not perform the identity transformation.

**Decision**

As performance is not considered a bottleneck, we decided not to check for the corner case of the identity transformation.


## Invariants / guarantees

* Both complete replacement and manipulation within a match are supported.
* At minimum, replacement by text is supported.
* The user is responsible for ensuring that node removal produces syntactically correct code.

## Related features

* [Rewrite semantics](rewrite-semantics.md)
* [Standard libraries](standard-libraries.md)

## Related tests

## Related code

## Notes

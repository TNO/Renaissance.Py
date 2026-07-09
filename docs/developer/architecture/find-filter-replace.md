{ #dev-architecture-code-find_filter_replace }

# Code architecture - Find, Filter, and Replace workflow

**Stable ID:** `ARCH-CODE-FIND_FILTER_REPLACE`

## Find

Given a find pattern, syntactic [matches](..\..\user\concepts\matching.md) within the codebase are located.

The find pattern could be specified using
* representation of parser
* grammar of the language
* concrete syntax

**Decision**

We have chosen concrete syntax.
As most developers are most familiar with the concrete syntax, it minimizes the learning curve and makes the tool easy to adopt.


## Filter

A [filter](..\..\user\concepts\filter.md) function checks a set of semantic properties to ensure correctness of the transformation.

[Rice's theorem](https://en.wikipedia.org/wiki/Rice%27s_theorem) states that all non-trivial semantic properties of programs, such as [halting](https://en.wikipedia.org/wiki/Halting_problem), are undecidable.

When a user combines multiple filter functions into a single filter function that user also becomes responsible for the diagnostics of the combination.

When a framework allows the combination of filter functions (under the `and` operator), the framework can also provide the diagnostics for the combination.

**Decision**

Filter functions have a human-readable description for diagnostic purposes.

We support undecisive filter results.
The framework should provide diagnostics for each matched location. Besides the location, the diagnostics should include
* in case of rejection, the human-readable description of the filter function that rejected the location, and
* in case of indecisive, the human-readable description of the filter functions that were indecisive.

The framework enables the combination (chaining) of filter functions.
A filter function will not be executed whenever an earlier filter function returns `false`.
Note that when a filter function returns `undecisive` the next filter function will be executed.


### Switch

Switch functionality would enable different replacements for different situations.
For example, depending on whether the placeholder `$$before` is empty in the match, replacement could be `f(1)` or `f($$before, 1)`, respectively.

Similar functionality can be achieved by using multiple filter functions for the different situations.

**Comparison**

Switch functionality offers faster execution performance and less code duplication.
Using multiple filters result in simpler logic and a smaller API, requiring less infrastructural development.

**Decision**

As execution performance is not an issue, switch functionality is not supported (for now).


## Manipulate

### Replace vs manipulate match

When a match is found, it can be completely replaced or manipulation can be performed on it.
Manipulations include the insertion of text before a placeholder and the replacement of a placeholder within the match.

Code owners typically prefer minimally invasive changes: layout should be preserved and comments should not be removed.
As white spaces and comments are ignored during the creation of an AST, manipulation within the match, instead of replacing the complete match, produces smaller diffs that are easier for code owners to review and accept.

**Decision**

We decide to support both the replacement of a complete match as manipulation within a match.

### Replacement text vs pattern

Replacing with text and with pattern have the following advantages:
 
Text 
+ enables unstructured text and migration to another programming language, i.e., transpilation.

Pattern 
+ enables enforcing the correctness of transformation by checking that the find and replacement patterns share a based type. 
+ enables correctly handling of syntax tokens, including separators, when placeholders are empty. To give some examples,
  * the keyword `else` should be absent when that branch has no statements.
  * in the function call `f($$before, 1)`, when the placeholder `$$before` is empty, the comma should be removed.

**Decision**

We decide to support at least the replacement by text.

### AST aware removal

When an AST node is removed, the result code might no longer be correct.
For example, removing the function call `f()` in the Python if statement 
```python
if cond:
    f()
```
results in invalid code.

Correctness of the final code is not ensured by replacement by text. 

**Decision**

The user is responsible for ensuring that removal of an AST node results in correct code.

For efficiency, we recommend that the [standard-libraries](standard-libraries.md#ast-aware-removal-of-node) contain for each language functionality for correct removal of an AST node in all situation. 
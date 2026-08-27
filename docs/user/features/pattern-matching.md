{ #feature-pattern-matching }
# Pattern matching

**Stable ID:** `FEATURE-PATTERN-MATCHING`

## User-facing summary
The system supports sequence-based, kind-based, and structural matching with placeholders and controllable matching criteria.

## Related concepts
- [Matching](../concepts/matching.md)

## Related images
- Local image directory: [pattern-matching-images/](pattern-matching-images/README.md)

# MISC

# Scenario: Independent of layout (whitespaces)

# Scenario: Independent of comments

Three cases
1. absent in pattern, present in code
2. present in pattern, absent in code
3. present in pattern, present in code, yet different content

# Scenario: Support of placeholders

* Placeholders are AST Nodes
* Support of explicit and implicit placeholders

# Scenario: Robustness for occurrence of implicit placeholders

* in strings, e.g. `"$X"`
* in comments, e.g., `/* $X */`.

# Scenario: Multiple occurrences of placeholders

* Equivalent AST nodes
* Access to all occurrences

# Scenario: Multiple assignments of placeholders

* E.g., in patterns like `$f($$before, $arg, $$after)`

# Legality of match-patterns

For exact matching, we currently accept all patterns.
In other words, no illegal `match` pattern exists.



-------------------------------------------------


1. Match functionality
   a. Elementary matching - "symbols with symbols" - representations of  integers, characters, etc.
   b. Basic matching - "code with code" - with(out) comment, with white spaces - note: python is sensitive for  indentation
   c. Single placeholder - "pattern with code" - pattern has only one instance of a single placeholder
   d. Multi placeholder - "pattern with code" - pattern has only one instance of a multi placeholder
   e. different placeholders - "pattern with code" with different placeholders (each placeholder occurs only once & only single assignment)
   f. constraint / recurring placeholder - "pattern with code" with single placeholder that occurs multiple times
   g. patterns with multi placeholders that can have multiple assignments
   h. mixed

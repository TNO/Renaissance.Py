{ #concept-matching }
# Matching

**Stable ID:** `CONCEPT-MATCHING`

## Purpose
Matching identifies occurrences of patterns in representations such as text or structured code.

## 1. Representation levels

### 1.1 Sequence of characters
- literal matching
- case-insensitive matching
- regular expressions

### 1.2 Kind matching
- numbers in text
- email addresses in text
- `if` statements in code

### 1.3 Pattern / structure matching
- words in text
- regex patterns in text
- matching brackets in code

Regular expressions cannot handle arbitrary nested, matching brackets.
A tool such as [comby](https://comby.dev/) can match nested delimiters, yet lacks semantic knowledge.

### 1.4 AST-based matching for code
- node kinds
- tree structure
- source correspondence

## 2. Pattern language

### 2.1 Concrete syntax
Patterns may use ordinary source notation already known to developers.

### 2.2 Groups, placeholders, and holes
- single placeholder: `$x`
- multi placeholder: `$$xs`

### 2.3 Matching constraints inside a pattern
Repeated occurrences of the same placeholder act as a back-reference style constraint.

## 3. Nested matches
- nested `if` statements and `for` loops in code
- nested parentheses such as `(a(b(c)))` in text-like structures

## 4. Multi-matches
Patterns can admit more than one valid decomposition, for example:

```text
f($$before, $arg, $$after)
```

Relevant strategies include eager, lazy, and all-possible matching.

## 5. Matching criteria
- full
- prefix
- anywhere
- first, next, and all

## Related images
- Local image directory: [matching/](matching/README.md)

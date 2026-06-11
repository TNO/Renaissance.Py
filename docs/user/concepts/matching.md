# Matching

**Stable ID:** `CONCEPT-MATCHING`

## Purpose
This document describes the concept of a match, i.e., when two objects are considered equal, 
and of finding matches that locates occurrences where this relation holds.

## 1.1 When do objects match?

The Cambridge dictionary describes match (_noun_) [EQUAL] as
> [a person or thing that is equal to another person or thing in strength, speed, or quality](https://dictionary.cambridge.org/dictionary/english/match).

Finding matches is not absolute but depends on the conceptual view of the objects.

For example, text can be conceptually viewed in different ways:
* **Granularity:** What is the smallest entity? E.g., character or word.
* **Structure:** Is the text a flat sequence or a hierarchy, with chapters, sections, and paragraphs?
* **Classification:** What classes of elements exist? E.g., nouns, verbs, numbers, email addresses, and questions.   
* **Equality:** When are two elements considered equal? E.g., is case relevant (e.g., `here`, `Here`, `HERE`)?

The different conceptual views lead to different matching outcomes. For example:
* `a` and `A` are different characters, but might represent the same letter.
* `here` and `there` are different words, but the sequence of characters `here` occurs within `there` under a character-based view.
* A chapter and a section might share the same title, e.g., `Introduction`.

[Table 1.1](#matching-table-text_examples) clearly illustrates the difference in finding matches, 
i.e., whether a needle occurs within a haystack,
<!---
   a query / search string within a text 
-->
for several conceptual views.

<a name="matching-table-text_examples">

*Table 1.1: Examples of whether a match is present under several conceptual views of text.*

| conceptual view of text | `a` within `A` | `here` within `there` |
| ----------------------- | -------------- | --------------------- |
| sequence of characters  | no             | yes                   |
| sequence of letters     | yes            | yes                   |
| sequence of words       | no             | no                    |

</a>

Text editors provide options that influence matching, such as case sensitivity, whole-word matching, and pattern-based descriptions using regular expressions, which correspond respectively to choices of equality, granularity, and classification.
See for example [Figure 1.1](#matching-equal-notepad++-find) that shows options supported by Notepad++.

<a name="matching-equal-notepad++-find">

![Find window of Notepad++](matching/matching-equal-notepad++-find.png)

*Figure 1.1 (CONCEPT-MATCHING): Selecting the desired text representation in the Find window of Notepad++.*

</a>




## representations of code


### 1.2 Kind matching
- numbers in text
- email addresses in text
- `if` statements in code

## 1.3 pattern / structure matching (text - regular expressions)


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

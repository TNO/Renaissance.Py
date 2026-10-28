<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Regular expressions in Python

{ #dev-architecture-environment-regular-expressions }

**Stable ID:** `ARCH-ENVIRONMENT-REGULAR-EXPRESSIONS`

This page summarises the capabilities and limitations of Python's `re` module and the practices we follow when using
regular expressions for searching and transforming text.
See the [`re` module documentation](https://docs.python.org/3/library/re.html) and the
[Regular Expression HOWTO](https://docs.python.org/3/howto/regex.html) for the full reference.

## Key conclusions

1. Regular expressions work on both `str` and `bytes`, but a `bytes` pattern matches bytes, not characters.
   Its results therefore depend on the encoding of the input, so `str` is the preferred default.
2. Python has no built-in transaction or batch mechanism for combining multiple changes.
   A single `re.sub` call applies all its matches against the original text,
   but combining several rules or edits requires custom logic.
3. Python has no built-in operation to modify a single group of a match.
   The replacement always covers the whole match;
   modifying a group is done by rebuilding the match, by using lookarounds, or by splicing group spans in a callback.

## Capabilities of `re`

<!-- MD060 is disabled because pymarkdown miscounts the width of `<` and `>` in code spans; RECHECK when pymarkdown is updated. -->
<!-- pyml disable md060-->

| Area                         | Support                                                                                                |
| ---------------------------- | ------------------------------------------------------------------------------------------------------ |
| Subject types                | `str` patterns on `str`; `bytes` patterns on bytes-like objects; the two cannot be mixed               |
| Functions                    | `search`, `match`, `fullmatch`, `finditer`, `findall`, `split`, `sub`, `subn`, `escape`, `compile`     |
| Match object                 | `group()`, `groups()`, `groupdict()`, `span(g)`, `start(g)`, `end(g)`, `lastgroup`, `expand(template)` |
| Groups                       | Capturing `(...)`, named `(?P<name>...)`, non-capturing `(?:...)`, backreferences `\1` and `(?P=name)` |
| Lookarounds                  | `(?=...)`, `(?!...)`, `(?<=...)`, `(?<!...)`; lookbehind must be fixed-width                           |
| Conditionals                 | `(?(id)...)`; see [Conditional patterns](#conditional-patterns)                                        |
| Backtracking control (3.11+) | Atomic groups `(?>...)` and possessive quantifiers `*+`, `++`, `?+`                                    |
| Flags                        | `IGNORECASE`, `MULTILINE`, `DOTALL`, `VERBOSE`, `ASCII`; inline `(?i)` or scoped `(?i:...)`            |
| Replacement                  | Template string (`\1`, `\g<name>`, `\g<0>`) or a callable that receives the match object               |
| Engine                       | Backtracking engine; recently used compiled patterns are cached                                        |

<!-- pyml enable md060-->
Bytes-like objects include `bytes`, `bytearray`, `memoryview`, and `mmap`.

## Limitations of `re`

The third-party [`regex`](https://pypi.org/project/regex/) package lifts the following limitations:

- No variable-width lookbehind, no `\K`, and no recursive patterns.
- No Unicode property classes such as `\p{L}` or `\p{Lu}`.
- A repeated group only keeps its last capture; `regex` offers `captures(g)` and `spans(g)` for all repetitions.
- No fuzzy matching and no matching timeout.

## Conditional patterns

A conditional `(?(id)yes-pattern|no-pattern)` chooses between two sub-patterns,
depending on whether a capturing group has participated in the match so far:

- if group `id` (a group number or a group name) has matched, the engine tries `yes-pattern`;
- otherwise, the engine tries `no-pattern`; the `|no-pattern` part is optional and defaults to the empty pattern.

The `|` separates the two branches, because alternation has the lowest precedence of all regular expression operators:
quantifiers bind tighter than concatenation, and concatenation binds tighter than alternation.
So `yes|no` means `(?:yes)|(?:no)`, not `ye(?:s|n)o`.

The following pattern matches an email address that is either enclosed in angle brackets or bare:
a closing `>` is required only when an opening `<` was matched.

```python
import re

pattern = re.compile(r"(<)?(\w+@\w+(?:\.\w+)+)(?(1)>|$)")

pattern.match("<user@host.com>")  # match: group 1 matched, so '>' is required
pattern.match("user@host.com")  # match: group 1 did not match, so the end of the string is required
pattern.match("<user@host.com")  # None: '<' without '>'
```

A conditional accepts at most two branches. Group the alternatives of a branch to use more of them:

```python
re.compile(r"(a)?(?(1)b|c|d)")  # re.PatternError: conditional backref with more than two branches
re.compile(r"(a)?(?(1)b|(?:c|d))")  # the no-pattern matches 'c' or 'd'
```

Python does not support lookaround conditions such as `(?(?=x)then|else)`;
use two opposite lookarounds instead: `(?=x)then|(?!x)else`.

Further reading:

- [Python `re` regular expression syntax](https://docs.python.org/3/library/re.html#regular-expression-syntax),
  entry `(?(id/name)yes-pattern|no-pattern)`
- [If-Then-Else Conditionals in Regular Expressions](https://www.regular-expressions.info/conditional.html)

## Strings, bytes, and encodings

- A `str` pattern matches decoded Unicode code points, so the file encoding only matters when decoding the file.
- A `bytes` pattern matches raw bytes:
  `.` matches a single byte, `\w`, `\d`, `\s` and case-insensitive matching are ASCII-only,
  and match positions are byte offsets instead of character offsets.
- UTF-8 is safe for ASCII-only `bytes` patterns: an ASCII byte never occurs inside a multi-byte UTF-8 sequence.
- UTF-16 and several legacy encodings (for example Shift-JIS) are not safe for `bytes` patterns,
  because ASCII byte values can occur inside multi-byte characters.

```python
import re

re.findall(r"\d+", "a12b3")  # ['12', '3']
re.findall(rb"\d+", b"a12b3")  # [b'12', b'3']
re.findall(r"\d+", b"a12")  # TypeError: cannot use a string pattern on a bytes-like object
```

## Transformations

### A single substitution

`re.sub` returns a new string, because strings are immutable.
All matches of a single call are found in the original text, so earlier replacements never affect later matches.

### Combining multiple rules

Combine the rules into one pattern with named alternatives and dispatch on `lastgroup`:

```python
rules = {"old": "new", "foo": "bar"}
pattern = re.compile("|".join(f"(?P<g{i}>{re.escape(k)})" for i, k in enumerate(rules)))
replacements = list(rules.values())
result = pattern.sub(lambda m: replacements[int(m.lastgroup[1:])], text)
```

Or collect edits as `(start, end, replacement)` against the original text, check for overlaps, and apply them in one pass:

```python
edits = [(m.start(), m.end(), f"print({m[1]})") for m in re.finditer(r"\bprint\s+(\w+)", text)]
edits += [(m.start(), m.end(), "range") for m in re.finditer(r"\bxrange\b", text)]

edits.sort()
parts, pos = [], 0
for start, end, replacement in edits:
    if start < pos:
        raise ValueError(f"overlapping edit at {start}")
    parts += [text[pos:start], replacement]
    pos = end
parts.append(text[pos:])
result = "".join(parts)
```

Collecting edits first enables conflict detection, previews, and applying all changes at once.

### Modifying groups

Rebuild the match with backreferences:

```python
s = "def foo(x):"
re.sub(r"(def )(\w+)(\()", r"\1new_name\3", s)  # replace group 2
re.sub(r"(def )(\w+)(\()", r"\1\2_v2\3", s)  # append to group 2
re.sub(r"(def )(\w+)(\()", r"\1_\2\3", s)  # prepend to group 2
```

Use `\g<1>0` instead of `\10` when a digit directly follows a backreference.

Restrict the match to the part to change with lookarounds:

```python
re.sub(r"(?<=def )\w+(?=\()", "new_name", s)
```

Splice the spans of one or more groups in a callback:

```python
def replace_groups(m: re.Match, replacements: dict) -> str:
    base, full = m.start(), m.group(0)
    edits = []
    for group, func in replacements.items():
        start, end = m.span(group)
        if start == -1:  # group did not participate in the match
            continue
        edits.append((start - base, end - base, func(m.group(group))))
    edits.sort()
    parts, pos = [], 0
    for start, end, replacement in edits:
        if start < pos:
            raise ValueError(f"overlapping groups at {start}")
        parts += [full[pos:start], replacement]
        pos = end
    parts.append(full[pos:])
    return "".join(parts)


re.sub(r"def (\w+)\((\w*)\)", lambda m: replace_groups(m, {1: str.upper, 2: lambda a: a + ": int"}), "def foo(x):")
# 'def FOO(x: int):'
```

When splicing group spans, take into account that:

- nested groups overlap, so modify either the outer or the inner group, not both;
- a repeated group only reports the span of its last repetition;
- an empty group has a zero-width span and acts as an insertion point;
- a group that did not participate in the match reports the span `(-1, -1)`.

A backreference such as `\1` or `(?P=name)` is not a group and has no span.
Wrap each backreference in its own (named) group to get its span:

```python
m = re.search(r"(?P<w>\w+) (?P<r1>(?P=w)) (?P<r2>(?P=w))", "say hey hey hey!")
m.span("w"), m.span("r1"), m.span("r2")  # (4, 7), (8, 11), (12, 15)
```

## Best practices

### Writing patterns

- Always write patterns as raw strings, for example `r"\d+"`.
- Use `re.VERBOSE` for complex patterns, so they can contain whitespace and comments.
- Prefer named groups over numbered groups for readability and stability.
- Escape literal and user-supplied text with `re.escape()`.
- Use `fullmatch` for validation; use `\A` and `\z` (`\Z` before Python 3.14) to anchor at the start and end of the whole string,
  because `^` and `$` change meaning with `MULTILINE`.
- Use non-capturing groups `(?:...)` when the capture is not needed.

### Text and encoding

- Prefer `str` and decode explicitly, for example `open(path, encoding="utf-8")`.
- Use `bytes` patterns only for byte offsets, `mmap`, or binary data, and only on UTF-8 input with ASCII patterns.
- Preserve line endings when rewriting files by opening them with `newline=""`,
  and handle a byte order mark explicitly, for example with the `utf-8-sig` encoding.

### Performance and safety

- Compile patterns that are reused, for example at module level.
- Avoid nested or ambiguous quantifiers such as `(a+)+` or `(.*)*`:
  they cause catastrophic backtracking, which is a denial-of-service risk on untrusted input.
  Use atomic groups or possessive quantifiers (Python 3.11+), or limit the input size.
- Prefer `finditer` over `findall` for large inputs or when match positions are needed.

### Applying transformations

- Use a callable replacement when the replacement requires logic.
- Use `subn` when the number of replacements is needed.
- Collect edits against the original text, check for overlaps, and apply them in a single pass.
- Modify specific groups by splicing their spans or by rebuilding the match with `\g<...>`.
- Write files safely: write to a temporary file and replace the original with `os.replace()`.

### When not to use regular expressions

- Do not use regular expressions to transform source code or other structured languages:
  they cannot reliably handle nesting, strings, and comments.
  Use a parser instead, such as `ast`, `tokenize`, `libcst`, or tree-sitter.
- Regular expressions remain useful within such tools for token-level checks or for matching inside the text of a node.

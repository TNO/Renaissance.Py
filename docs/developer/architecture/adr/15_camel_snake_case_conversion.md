# 15 - camelCase/snake_case Conversion and Digit-as-Word Naming

Status: Accepted

Date: 2026-09-09

Authors:

- francesco.pezzella15@gmail.com
- pierre.vandelaar@tno.nl

## Context

`renaissance.utils.text_utils` provides `snake_case()`, used by `PythonRefactoring.process()` to
resolve a recipe class name to its module path via `importlib`. A sibling `camel_case()` helper had
no caller besides its own tests. Issue #146 asked whether `camel_case()` should be removed, and
whether `snake_case()` should split a word on a digit (`Unit2Pytest` -> `unit2pytest`) or keep the
digit attached (`unit2_pytest`).

A well-supported library ([`camel-converter`](https://pypi.org/project/camel-converter/)) was
considered instead of a hand-rolled converter, but its default `to_snake()` splits every uppercase
letter individually, breaking multi-letter acronyms this codebase relies on (see Example). PR #147
kept the project's own implementation and removed `camel_case()` as dead code.

Two recipes used a digit as a stand-in for "to": `taut2pyunit.py` (`Taut2Pyunit`) and
`unit2pytest.py` (`Unit2Pytest`). PR #147 review comments (Pierre, Quinn) established that a digit
standing in for a word is not itself a word. Pierre approved Quinn's suggestion, on the PR #147
review thread, to spell `Pyunit` out fully as well (`TautToPythonUnittest`).

## Decision

- Remove `camel_case()` — dead code.
- Keep `snake_case()` over `camel-converter` — the library incorrectly splits multi-letter acronyms
  (see Example).
- **Rule A** (`snake_case()` itself): a digit stays attached to its word, never splits on its own —
  `Base64Encode` -> `base64_encode`, `HTML5Parser` -> `html5_parser`. Unchanged from PR #147.
- `snake_case()` is also robust on input that is already snake_case — it leaves it unchanged
  (`already_snake` -> `already_snake`), so it is safe to call on a name without checking its casing
  first.
- **Naming guideline** (for names contributors choose, e.g. recipe/class/function names): avoid
  using a digit as a stand-in for a word (no `2` for "to"). Spell it out. Applied to every current
  offender:
  - `Taut2Pyunit` -> `TautToPythonUnittest` (`taut_to_python_unittest.py`)
  - `Unit2Pytest` -> `UnitToPytest` (`unit_to_pytest.py`)
  - `signature2id` -> `signature_to_id`

## Implementation notes

- `src/renaissance/utils/text_utils.py`: `snake_case()` (Rule A), `camel_case()` removed.
- `src/renaissance/recipes/python_refactoring.py:39`: `PythonRefactoring.process()` resolves
  `class_name` -> `renaissance.recipes.<snake_case(class_name)>`; names following the guideline
  above resolve correctly by construction (`snake_case("TautToPythonUnittest")` ->
  `taut_to_python_unittest`).
- Renamed to follow the guideline, with their tests and feature steps: the two recipes above, and
  `signature2id()`'s one caller (`integrations/tree_sitter/visualizer.py`).
  `simplify_renaissance.py`'s `white_list_pattern` was updated to match — the old
  `"unit2pytest"` pattern no longer matched PR #147's already-underscored filename, a latent bug
  fixed as a side effect.

## Example

```bash
uv run --with camel-converter python -c "
from camel_converter import to_snake
for s in ['HTMLParser', 'HTML5Parser', 'Base64Encode']:
    print(s, '->', to_snake(s))
"
```

| Input          | `camel-converter` | `snake_case()`  |
| -------------- | ----------------- | --------------- |
| `HTMLParser`   | `h_t_m_l_parser`  | `html_parser`   |
| `HTML5Parser`  | `h_t_m_l5_parser` | `html5_parser`  |
| `Base64Encode` | `base64_encode`   | `base64_encode` |

## Rationale

- The acronym-grouping regex matches this codebase's actual identifiers; a character-by-character
  library default does not.
- No general convention for digit-as-word-abbreviation was found — letting `snake_case()` guess
  would be unreliable, so it's a naming guideline for reviewers to apply by eye instead.

## Consequences

Positive:

- No new dependency; correct on this codebase's acronym-bearing names.
- Recipe names read as sentences; `PythonRefactoring.process()` resolution keeps working by
  construction.

Negative:

- `snake_case()` is a second implementation of a "solved" problem, needing its own tests (covered,
  ADR 08).
- The naming guideline can't be enforced automatically — relies on review.

## Alternatives considered

- Adopt `camel-converter` — rejected: wrong on multi-letter acronyms.
- Teach `snake_case()` to treat digits as word-abbreviations — rejected: ambiguous, no general rule
  found.

## Related decisions

- ADR 08 (Test architecture) — the parametrized-test convention followed by
  `test/utils/test_text_utils.py`.

---

Revision history:

- 2026-09-09: Created from issue #146 / PR #147 discussion.
- 2026-09-09: `TautToPyunit` -> `TautToPythonUnittest`, following Pierre's approval on the PR #147
  review thread.

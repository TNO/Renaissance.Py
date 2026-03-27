# 08 - Test Architecture

Status: Accepted

Date: 2026-03-27

Authors:
 - jinmin.hu@capgemini.com
 - huub.joosten@capgemini.com
 - luna.li@capgemini.com
 - paul.nelissen@esi.nl
 - pierre.vandelaar@tno.nl

## Table of contents

- [Context](#context)
- [Decision](#decision)
- [Implementation notes](#implementation-notes)
- [Example](#example)
- [Rationale](#rationale)
- [Consequences](#consequences)
- [Alternatives considered](#alternatives-considered)
- [Related decisions](#related-decisions)

## Context

To ensure maintainability and extensibility a test architecture is crucial. The project needs a coherent set of
testing frameworks covering behaviour-driven tests, unit tests, performance benchmarks, and inline documentation
examples. The choice of frameworks has implications for test discovery, fixture sharing, CI integration, and the
ability to express the domain-specific requirements listed below.

### Functionalities that must be tested

**Code matching**
- Independent of layout (whitespace) and comments (presence, absence, content).
- Support for placeholders; placeholders are AST nodes.
- Support for explicit and implicit placeholders.
- Robustness: implicit placeholders must not be triggered inside strings (`"$X"`) or
  comments (`/* $X */`).
- Multiple occurrences of the same placeholder express an equality constraint
  (e.g., `$f; var = $f;`).
- Multiple assignments of placeholders (e.g., `$f($$before, $arg, $$after)`).

**Placeholder matching rules**
- A placeholder matches at the *highest* AST node whose concrete syntax reduces to a single name
  (function `getPlaceholderName` is applied recursively).
- The same placeholder may be bound to nodes of different AST classes within one pattern
  (e.g., `$type` in `$type* ptr = new $type()` binds to `IASTNamedTypeSpecifier` then `IASTTypeId`).
  Comparison must therefore be structural, not class-based.

**Equivalent code matching**
- Readability variants: `1_000_000` ≡ `1000000`.
- Numeric bases: `0xFF` ≡ `255`.
- Scientific notation: `1E2` ≡ `100`.
- String delimiters: `"ape"` ≡ `'ape'`.
- String concatenation: `"con" "cat"` ≡ `"concat"`.
- Symmetric operators: `0 == x` matches `x == 0`.
- Equivalent initialisation forms (C++): `int x = 1;` matches `int x { 1 };`.

**Find functionality**
- Find by kind (nested): e.g., find all `if` statements; a found match may contain another found match.
- Language-agnostic kinds: definition, statement, expression, declaration, …
- Parser-specific kinds: e.g., `IASTIfStatement`.
- Find by AST pattern (nested): e.g., `if ($x == MAX) { $$stmts; }`.
- Find consecutive (non-overlapping): `find "aa" in "aaa"` → one match;
  `find "aa" in "aaaa"` → two non-overlapping matches.

**Navigation functionality**
- AST structure: parent & ancestors, children & descendants, siblings.
- Usage: definition / forward declaration → references (current file / analysis unit only).
- Inheritance: base ↔ derived classes.

**Transformation functionality**
- The encoding of a file must never change.
- File/directory metadata may only change when an actual transformation occurred;
  analysis or a failing filter are not sufficient.
- *Offset-based* batch modifications:
  - Insert and replace (remove = replace with `""`).
  - Containment rule: contained operations are ignored.
  - Consistency rule: overlapping operations are forbidden.
- *AST-based* batch modifications:
  - Prepend, append, replace, around (e.g., for matching brackets).
  - Containment rules:
    - A replace on a node hides all operations on its descendants (prepend/append/around are unaffected).
    - A prepend to a node is always before a prepend to any descendant.
    - An append to a node is always after an append to any descendant.
  - Sequence rule: an append to sibling N is always before a prepend to sibling N+1.
- Find + filter (possibly multiple) + replace (whole match replaced).
- Replace recursively (AST nodes bound to placeholders are also modified).
- Find + filter (possibly multiple) + modify:
  - Multiple operations on a single find result.
  - Any AST node reachable via navigation may be modified, not only nodes contained in the match.

## Decision

Adopt the following test framework stack:

| Purpose | Framework |
|---------|-----------|
| BDD / acceptance tests | **pytest-bdd** |
| Unit tests | **pytest** |
| Performance benchmarks | **pytest-benchmark** |
| Inline documentation examples | **doctest** |
| Assertion style | **PyHamcrest** (`assert_that`) |

pytest-bdd is chosen over Behave and Robot Framework (see [Alternatives considered](#alternatives-considered)).

## Implementation notes

- All test files follow pytest naming conventions (`test_*.py` or `*_test.py`).
- BDD feature files are placed under `features/` and steps under `features/steps/`.
- Fixtures are defined with `@pytest.fixture`; shared fixtures live in `conftest.py`.
- Parametrised tests use `@pytest.mark.parametrize`.
- Coverage is measured with `pytest-cov` (`--cov-report=term-missing`).
- All pytest configuration lives under `[tool.pytest.ini_options]` in `pyproject.toml`.
- Performance baselines are stored in `.benchmarks/` (git-ignored by default).

## Example

```python
import pytest
from hamcrest import assert_that, is_, contains_inanyorder

@pytest.fixture
def sut():
    return Matcher()

class TestMatcherPlaceholder:
    def test_placeholder_matches_highest_ast_node(self, sut):
        pattern = pattern_factory("$x;", SyntacticKind.STATEMENT)
        result = sut.find(parse("a = f(1, 2+3);"), pattern)
        assert_that(result, is_(non_empty()))

    @pytest.mark.parametrize("source,expected", [
        ("1_000_000", "1000000"),
        ("0xFF",      "255"),
        ('"ape"',     "'ape'"),
    ])
    def test_equivalent_literals(self, sut, source, expected):
        assert_that(sut.are_equivalent(source, expected), is_(True))
```

```gherkin
# features/find.feature
Feature: Find functionality
  Scenario: Find nested if statements
    Given a source file containing nested if statements
    When I search for if statements
    Then each outer match may contain inner matches
```

## Rationale

pytest is the de-facto standard for Python unit testing, so all other frameworks are chosen for their
integration with it. pytest-bdd shares pytest fixtures, the CLI, plugins, and reporting — eliminating the
overhead of a separate test runner. pytest-benchmark plugs into the same run. doctest keeps examples
in sync with the documentation automatically. PyHamcrest makes assertions self-documenting and produces
readable failure messages.

## Consequences

Positive:
- Single test runner (`pytest`) for all test kinds: BDD, unit, benchmark, doctest.
- Shared fixtures across BDD steps and unit tests via `conftest.py`.
- Rich plugin ecosystem (`pytest-cov`, `pytest-mock`, `pytest-bdd`, `pytest-benchmark`).
- Seamless CI integration.
- Expressive, readable assertions via PyHamcrest.

Negative:
- pytest-bdd's Gherkin support is slightly less mature than Behave's.
- Multiple frameworks must be kept in sync (versions, plugins).
- Writing and maintaining BDD step definitions adds overhead over plain unit tests.

## Alternatives considered

**BDD framework**

| Framework | Assessment |
|-----------|------------|
| **pytest-bdd** ✓ | Integrates with pytest (shared fixtures, CLI, plugins). Active since 2013. |
| Behave | Standalone; no shared fixtures with pytest. Very mature (2011). Rejected due to split runner. |
| Robot Framework | Full automation framework; steep learning curve; overkill for BDD only. |
| Lettuce | Declining community; minimal updates. Rejected. |

**Unit testing**
- `unittest` (stdlib) — rejected: more boilerplate, no plugin ecosystem, less expressive assertions.

**Assertion style**
- Plain `assert` — rejected in favour of PyHamcrest for richer failure messages and composable matchers.

## Related decisions

- See ADR 09 (Property-based tests) for the use of Hypothesis alongside pytest.
- See ADR 10 (Type hierarchy) for the `SyntacticKind` taxonomy referenced in find-functionality tests.
- See ADR 12 (Patterns are not nodes) for the `Pattern` type used in matching tests.

---

Revision history:
- 2026-03-27: Converted GitHub issue #08 to ADR template; expanded all functionality requirements.

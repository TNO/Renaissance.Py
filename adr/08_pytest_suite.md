# 08 - Pytest Suite

Status: Accepted

Date: 2026-03-27

Authors:
 - jinmin.hu@capgemini.com
 - huub.joosten@capgemini.com
 - luna.li@capgemini.com
 - paul.nelissen@esi.nl
 - pierre.vandelaar@tno.nl

## Context

The project requires a coherent and mature testing strategy that integrates well with the Python ecosystem. A number of 
testing frameworks exist, but the choice of framework has implications for test discovery, fixture management, 
parametrization, plugin availability, and CI integration.

## Decision

pytest is adopted as the testing and linting facilities framework for this project. It covers a wide range of testing 
needs and is coherent with the Python ecosystem. It is a mature and widely adopted testing framework that provides a 
rich set of features for writing and running tests.

## Implementation notes

- All test files are named `test_*.py` or `*_test.py` to allow pytest auto-discovery.
- Fixtures are defined using the `@pytest.fixture` decorator.
- Parametrised tests use `@pytest.mark.parametrize`.
- Coverage is measured with `pytest-cov` and reported via `--cov-report=term-missing`.
- The `pyproject.toml` file holds all pytest configuration under `[tool.pytest.ini_options]`.

## Example

```python
import pytest
from hamcrest import is_, assert_that 

@pytest.fixture
def sut():
    return MyClass()

class TestMyClass:
def test_my_function(sut):
    assert_that(sut.my_function(), is_( expected_value))

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
])
def test_double(input, expected):
    assert_that(sut.fun(input) , is_(less_than(expected)))
```

## Rationale

pytest covers a wide range of testing and linting facilities that is coherent with the Python ecosystem. It is a mature
and widely adopted testing framework that provides a rich set of features for writing and running tests. Compared to 
the standard `unittest` module it offers simpler syntax, powerful fixtures, and a rich plugin ecosystem.

## Consequences

Positive:
- expressive test by using hamcrest in combination with pytest.
- Powerful fixture system enabling dependency injection in tests.
- Rich plugin ecosystem (e.g., `pytest-cov`, `pytest-mock`, `pytest-bdd`).
- Seamless integration with CI pipelines and coverage tools.

Negative:
- Adds an external dependency not present in the standard library.
- Some pytest-specific idioms (e.g., fixtures) may be unfamiliar to developers used to `unittest`.

## Alternatives considered

- `unittest` — rejected because it requires more boilerplate and lacks the plugin ecosystem and expressive assertion syntax of pytest.
- `nose2` — rejected as it is less actively maintained and has a smaller community than pytest.

## Related decisions

- See ADR 09 (Property-based tests) for the use of hypothesis alongside pytest.

---

Revision history:
- 2026-03-27: Converted to ADR template and clarified decision.

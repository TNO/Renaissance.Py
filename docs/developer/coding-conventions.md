# Coding conventions

This page captures conventions that are smaller in scope than an [architecture decision](architecture/adr/README.md):
naming, formatting, and other day-to-day coding habits rather than design decisions.

We follow the standard Python coding conventions,
such as [PEP 8](https://peps.python.org/pep-0008/) and [PEP 257](https://peps.python.org/pep-0257/).
This coding conventions are enforced via `ruff`.

## Naming conventions

Do not use digits as abbreviations for words (e.g. `2` for "to", `4` for "for").

```python
# Good
def convert_ast_to_cst(node): ...


# Bad
def convert_ast2cst(node): ...
```

## Disabling checks

Disable a lint or type check locally, on the specific line that triggers it — not for a whole file or project.
Add a comment explaining why the check is disabled.

If the check is disabled to work around a bug in the current tooling rather than a deliberate exception,
add `RECHECK when <tool> is updated` to the comment, so the suppression can be removed once the tooling is fixed.

```python
value = some_call()  # noqa: E501 RECHECK when ruff is updated (false positive on this line, see ruff#1234)
```

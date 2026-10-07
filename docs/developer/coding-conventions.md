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

## Lint and type-check budgets

`pyproject.toml` configures the `ruff` rules and the `pyright` mode that the whole repository already passes,
so CI fails on any new violation of those.
The stricter settings we still want — all `ruff` rules and `pyright`'s `strict` mode — are not enabled there yet,
because the existing issues would fail every build.
Instead of disabling those checks, their issues are *budgeted* by `tools/lint_budget.py`:

* the strict settings live in the script (`ruff --select ALL`, minus the rules `pyproject.toml` deliberately ignores)
  and in `pyrightconfig.strict.json`;
* `lint-budget.json` records how many issues of each kind (`ruff` rule code, `pyright` rule name) currently exist;
* CI runs `python tools/lint_budget.py --check` and fails when a pull request exceeds the budget of any kind,
  so no new issue of any kind can be introduced;
* a pull request that *lowers* a count passes: the budget is a ceiling, never a quota;
* run `python tools/lint_budget.py` locally after fixing issues to lower the budget to the new counts, or leave it:
  after the merge — and once a week — the `lint budget` workflow runs the script on `main` and opens an auto-merging
  pull request with the lowered `lint-budget.json`, so the counts can only ratchet down;
* `--init` records the current counts as the budget; use it only for the first run or an approved exception.

The `lint budget` workflow opens its pull request with a GitHub App token, because the checks of a pull request
opened with the default `GITHUB_TOKEN` are never triggered, so auto-merge would wait for them forever.
Configure it with the `LINT_BUDGET_APP_CLIENT_ID` repository variable and the `LINT_BUDGET_APP_PRIVATE_KEY`
repository secret of an app with `contents` and `pull-requests` write access that is installed on this repository;
until then the workflow falls back to `GITHUB_TOKEN` and its pull request has to be checked and merged by hand.
Auto-merge also has to be allowed in the repository settings.
The commit is written through the GitHub API (`sign-commits`), so GitHub signs it on the app's behalf and the
"commits must have verified signatures" rule accepts it; a plain `git push` from the runner cannot be signed.

The app itself needs no code or hosting: it is a registration that only hands out short-lived tokens.
It may be owned by a personal account — create it under <https://github.com/settings/apps/new> with the webhook
disabled, "Where can this app be installed" set to **Any account**, and the two repository permissions above.
Installing it on `TNO/Renaissance.Py` then raises a request that a `TNO` owner has to approve.
An owner should transfer the app to the `TNO` organisation afterwards, so it outlives its creator's account.

CI checks the pull request merged with `main`, so the counts can exceed the budget because of issues
that arrived on `main` after the branch was created. Merge `main` into the branch and re-run the script.

Once every count has reached zero, the script says so: move the strict settings into `pyproject.toml`
and delete `lint-budget.json`, `pyrightconfig.strict.json`, `tools/lint_budget.py` and the CI step.

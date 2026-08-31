"""Shared fixtures for the refactoring recipe test suite."""

import textwrap
from collections.abc import Callable
from typing import cast

import pytest
from pytest_mock import MockerFixture

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.refactoring.type_var_check import PEP_695_MINIMUM, TypeVarCheck


@pytest.fixture
def make_recipe(mocker: MockerFixture) -> Callable[[type[PythonRefactoring], str], PythonRefactoring]:
    """Build a `recipe_cls` instance against in-memory, dedented source text.

    `PythonFactory.create` is mocked so nothing touches the filesystem. Shared by every
    refactoring recipe's tests instead of each reimplementing this setup - cast the result
    to the concrete recipe type if you need attributes/methods beyond PythonRefactoring's own.
    """

    def _make(recipe_cls: type[PythonRefactoring], text: str, filename: str = "x.py") -> PythonRefactoring:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code),
        )
        subject = recipe_cls(filename)
        subject.in_memory = True
        return subject

    return _make


@pytest.fixture
def create_type_var_check(make_recipe: Callable[[type[PythonRefactoring], str], PythonRefactoring]) -> Callable[[str], TypeVarCheck]:
    """Like `make_recipe`, but pinned to Python 3.12+.

    So PEP 695-conversion tests don't depend on whatever pyproject.toml happens to be found
    from the ambient cwd.
    """

    def _create(text: str) -> TypeVarCheck:
        subject = cast(TypeVarCheck, make_recipe(TypeVarCheck, text))
        subject.min_python_override = PEP_695_MINIMUM
        return subject

    return _create

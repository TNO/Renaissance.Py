# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Shared fixture for the TypeVarCheck tests."""

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.recipes.type_var_check import PEP_695_MINIMUM, TypeVarCheck


@pytest.fixture
def create_type_var_check(mocker: MockerFixture) -> Callable[[str], TypeVarCheck]:
    """Build a TypeVarCheck for in-memory, dedented source text, with min_python 3.12 so PEP 695 conversion is enabled.

    `PythonFactory.create` is mocked so nothing touches the filesystem.
    """

    def _create(text: str) -> TypeVarCheck:
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonCstNode.load_from_text(textwrap.dedent(text), "x.py"),
        )
        subject = TypeVarCheck(Path("x.py"))
        subject.in_memory = True
        subject.min_python = PEP_695_MINIMUM
        return subject

    return _create

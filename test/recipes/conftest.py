# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Shared fixture for the TypeParameterCheck tests."""

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.recipes.type_parameter_check import TypeParameterCheck


@pytest.fixture
def create_type_parameter_check(mocker: MockerFixture) -> Callable[[str], TypeParameterCheck]:
    """Build a TypeParameterCheck for in-memory, dedented source text.

    `PythonFactory.create` is mocked so nothing touches the filesystem.
    """

    def _create(text: str) -> TypeParameterCheck:
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonCstNode.load_from_text(textwrap.dedent(text), "x.py"),
        )
        subject = TypeParameterCheck(Path("x.py"))
        subject.in_memory = True
        return subject

    return _create

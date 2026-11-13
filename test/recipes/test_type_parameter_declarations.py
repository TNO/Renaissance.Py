# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for renaissance.recipes.type_parameter_declarations."""

from typing import cast

import libcst as cst
import pytest
from hamcrest import assert_that, equal_to

from renaissance.recipes.type_parameter_declarations import declaration_argument_names


class TestDeclarationArgumentNames:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("declaration", "expected"),
        [
            pytest.param('T = TypeVar("T")', set[str](), id="the-type-parameters-own-name-is-skipped"),
            pytest.param('T = TypeVar("T", bound=Shape)', {"Shape"}, id="keyword-argument"),
            pytest.param('T = TypeVar("T", Shape, Other)', {"Shape", "Other"}, id="constraints"),
            pytest.param('T = TypeVar("T", bound=np.integer)', {"np"}, id="attribute-reads-only-its-root"),
            pytest.param('T = TypeVar("T", bound="Shape")', {"Shape"}, id="string-is-a-forward-reference"),
            pytest.param('T = TypeVar("T", bound="not valid(")', set[str](), id="string-that-is-not-an-expression"),
            pytest.param('T = TypeVar("T", int, str)', set[str](), id="built-ins-are-left-out"),
            pytest.param('T = TypeVar("T", **options)', {"options"}, id="mapping-argument"),
        ],
    )
    def test_returns_the_non_builtin_names_the_arguments_use(self, declaration: str, expected: set[str]) -> None:
        """Verify the names the arguments read are returned, with the declared name and the built-ins left out."""
        line = cast("cst.SimpleStatementLine", cst.parse_statement(declaration))

        assert_that(declaration_argument_names(cast("cst.Assign", line.body[0])), equal_to(expected))

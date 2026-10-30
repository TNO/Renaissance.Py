# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for renaissance.utils.cst_utils."""

from typing import cast

import libcst as cst
import pytest
from hamcrest import assert_that, equal_to

from renaissance.utils.cst_utils import assigned_names, module_statements, names_read_by


class TestNamesReadBy:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("expression", "expected"),
        [
            pytest.param("x", {"x"}, id="name"),
            pytest.param("f(a, key=b)", {"f", "a", "b"}, id="keyword-argument-name-is-not-a-read"),
            pytest.param("np.integer", {"np"}, id="attribute-name-is-not-a-read"),
            pytest.param("a.b.c(d)", {"a", "d"}, id="attribute-chain-reads-only-its-root"),
            pytest.param("int | str", {"int", "str"}, id="built-ins-are-included"),
        ],
    )
    def test_returns_the_names_an_expression_reads(self, expression: str, expected: set[str]) -> None:
        """Verify every name read is returned, but neither an attribute's own name nor a keyword argument's name."""
        assert_that(names_read_by(cst.parse_expression(expression)), equal_to(expected))


class TestAssignedNames:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("statement", "expected"),
        [
            pytest.param("x = 1", {"x"}, id="plain"),
            pytest.param("x = y = 1", {"x", "y"}, id="chained"),
            pytest.param("x: int = 1", {"x"}, id="annotated-leaves-the-annotation-out"),
            pytest.param("a, b = 1, 2", {"a", "b"}, id="tuple-target"),
            pytest.param("[a, (b, c)] = value", {"a", "b", "c"}, id="nested-targets"),
        ],
    )
    def test_returns_the_names_the_targets_bind(self, statement: str, expected: set[str]) -> None:
        """Verify every name in the targets is returned, including inside tuple or list targets."""
        line = cast("cst.SimpleStatementLine", cst.parse_statement(statement))

        assert_that(assigned_names(cast("cst.Assign | cst.AnnAssign", line.body[0])), equal_to(expected))


class TestModuleStatements:
    """See module docstring."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            pytest.param("a = 1\nb = 2\n", ["Assign", "Assign"], id="one-per-line"),
            pytest.param("a = 1; b = 2\n", ["Assign", "Assign"], id="one-per-small-statement"),
            pytest.param("a = 1\nif a:\n    b = 2\n", ["Assign", "If"], id="compound-statement-is-one-item"),
        ],
    )
    def test_yields_the_top_level_statements_in_order(self, source: str, expected: list[str]) -> None:
        """Verify a line of several small statements gives one item each and a compound statement gives one in all."""
        statements = [type(statement).__name__ for statement in module_statements(cst.parse_module(source))]

        assert_that(statements, equal_to(expected))

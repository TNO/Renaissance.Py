# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for PythonCstNode.references and referenced_by, resolved with libcst's scope analysis."""

from typing import TYPE_CHECKING

import pytest
from hamcrest import assert_that, contains_inanyorder, equal_to

from renaissance.integrations.python.ast.cst_node import PythonCstNode

# TODO(FrancescoPezzella): Replace with a lazy import in Python 3.15.
#  https://github.com/TNO/Renaissance.Py/issues/275
if TYPE_CHECKING:
    from collections.abc import Iterator

HEADER = 'from typing import Generic, Literal, TypeAlias, TypeVar, cast\nT = TypeVar("T")\n'


def _load(body: str) -> PythonCstNode:
    """Parse HEADER followed by body into a PythonCstNode tree."""
    return PythonCstNode.load_from_text(HEADER + body, "refs.py")


def traverse(node: PythonCstNode) -> Iterator[PythonCstNode]:
    """Yield node and all its descendants, depth first."""
    yield node
    for child in node.children:
        yield from traverse(child)


def _declared_t(root: PythonCstNode) -> PythonCstNode:
    """Return the Name node that `T = TypeVar("T")` assigns."""
    return next(
        node
        for node in traverse(root)
        if node.parser_kind == "Name" and node.signature == "T" and node.parent is not None and node.parent.parser_kind == "AssignTarget"
    )


class TestPythonCstReferences:
    """References between a module-level name and its uses."""

    @pytest.mark.parametrize(
        ("body", "expected_uses"),
        [
            pytest.param("def b(x: T) -> T: ...\n", ["T", "T"], id="plain-names"),
            pytest.param('def b(x: "T") -> None: ...\n', ['"T"'], id="whole-string-annotation"),
            pytest.param('def b(x: "list[T]") -> None: ...\n', ['"list[T]"'], id="string-inside-annotation"),
            pytest.param('def b(x: list["T"]) -> None: ...\n', ['"T"'], id="nested-string"),
            pytest.param('def b(x: object) -> None:\n    cast("T", x)\n', ['"T"'], id="cast-in-body"),
            pytest.param("class Box(Generic[T]): ...\n", ["T"], id="generic-class-base"),
            pytest.param(
                'A: TypeAlias = "list[T]"\n',
                ['"list[T]"'],
                id="type-alias-string",
                marks=pytest.mark.xfail(reason="libcst's ScopeProvider doesn't read the string value of a TypeAlias.", strict=True),
            ),
        ],
    )
    def test_definition_and_uses_point_at_each_other(self, body: str, expected_uses: list[str]) -> None:
        """Every use of T is in T's referenced_by, and each of those uses references T's definition."""
        declared = _declared_t(_load(body))

        uses = [reference.node for reference in declared.referenced_by]

        assert_that([use.signature for use in uses], contains_inanyorder(*expected_uses))
        for use in uses:
            assert_that([reference.node for reference in use.references], equal_to([declared]))

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param("def b[T](x: T) -> T: ...\n", id="pep695-parameter"),
            pytest.param('def b[T](x: "T") -> "list[T]": ...\n', id="pep695-parameter-in-strings"),
            pytest.param("def outer[T](x: T) -> T:\n    def inner(y: T) -> T:\n        return y\n    return inner(x)\n", id="closure"),
            pytest.param("def outer() -> None:\n    def inner[T](x: T) -> T:\n        return x\n", id="nested-pep695-function"),
            pytest.param("def b() -> None:\n    T = 1\n    print(T)\n", id="local-variable"),
            pytest.param('d = {}\nd["T"]\n', id="dict-key-string"),
            pytest.param('def b(x: Literal["T"]) -> None: ...\n', id="literal-string"),
        ],
    )
    def test_uses_bound_to_another_name_are_not_references(self, body: str) -> None:
        """A T that resolves to a type parameter, a local variable or a plain string is not a use of the module-level T."""
        assert_that(_declared_t(_load(body)).referenced_by, equal_to([]))

    @pytest.mark.parametrize(
        ("body", "expected_uses"),
        [
            pytest.param("def b(x: T) -> T: ...\n", ["T", "T"], id="annotations"),
            pytest.param('def b(x: "list[T]") -> None: ...\n', ['"list[T]"'], id="string-annotation"),
            pytest.param('y = cast("T", 1)\n', ['"T"'], id="cast"),
            pytest.param("w = T\n", [], id="evaluated-at-once"),
        ],
    )
    def test_lazily_evaluated_use_above_the_declaration_is_a_reference(self, body: str, expected_uses: list[str]) -> None:
        """An annotation or type hint above `T = TypeVar("T")` is a use of it; a value read there at once is not."""
        root = PythonCstNode.load_from_text(
            f'from __future__ import annotations\nfrom typing import TypeVar, cast\n{body}T = TypeVar("T")\n', "refs.py"
        )
        declared = _declared_t(root)

        uses = [reference.node for reference in declared.referenced_by]

        assert_that([use.signature for use in uses], contains_inanyorder(*expected_uses))
        for use in uses:
            assert_that([reference.node for reference in use.references], equal_to([declared]))

    def test_import_reports_which_name_each_use_refers_to(self) -> None:
        """An import binding several names lists the uses of each, with the imported name in the reference properties."""
        root = _load('def b(x: object) -> None:\n    cast("int", x)\n')
        import_from = next(node for node in traverse(root) if node.parser_kind == "ImportFrom")

        names = [(str(reference.properties["name"]), reference.node.signature) for reference in import_from.referenced_by]

        assert_that(sorted(names), equal_to([("TypeVar", "TypeVar"), ("cast", "cast")]))

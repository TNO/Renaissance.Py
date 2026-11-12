# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for finding AST nodes by a NodeProtocol predicate."""

from renaissance.core.model import SemanticKind, find_nodes
from renaissance.integrations.python.ast.rst_node import PythonRstNode


def test_find_nodes_accepts_protocol_predicate() -> None:
    """AI: Assert find_nodes locates nodes matching an arbitrary NodeProtocol predicate."""
    root = PythonRstNode.load_from_text("def f():\n    return 1\n")

    functions = find_nodes(root, lambda node: node.semantic_kind is SemanticKind.FUNCTION)

    assert len(functions) == 1

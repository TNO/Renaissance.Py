# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Helpers over the libcst tree of one module: its top-level statements, the names they read or bind and the comment trailing a line."""

from collections.abc import Iterator

import libcst as cst


def module_statements(module: cst.Module) -> Iterator[cst.BaseSmallStatement | cst.BaseCompoundStatement]:
    """Yield the module's top-level statements in order, one per small statement of a line like `a = 1; b = 2`."""
    for statement in module.body:
        if isinstance(statement, cst.SimpleStatementLine):
            yield from statement.body
        else:
            yield statement


def trailing_of_sole_statement(module: cst.Module, statement: cst.BaseSmallStatement) -> cst.TrailingWhitespace | None:
    """Return the whitespace and comment trailing the line of statement in module, or None if the line holds others."""
    for line in module.body:
        if isinstance(line, cst.SimpleStatementLine) and len(line.body) == 1 and line.body[0] is statement:
            return line.trailing_whitespace
    return None


class _NameCollector(cst.CSTVisitor):
    """Collect the names an expression reads: every `Name` except an attribute's or a keyword argument's own name."""

    def __init__(self) -> None:
        """Start with no names collected."""
        super().__init__()
        self.names: set[str] = set()

    def visit_Name(self, node: cst.Name) -> None:  # noqa: N802 - libcst dispatches on this exact name
        """Record the name."""
        self.names.add(node.value)

    def visit_Attribute(self, node: cst.Attribute) -> bool:  # noqa: N802 - libcst dispatches on this exact name
        """Visit only the attribute's object: in `np.integer`, `integer` is not a name read here."""
        node.value.visit(self)
        return False

    def visit_Arg(self, node: cst.Arg) -> bool:  # noqa: N802 - libcst dispatches on this exact name
        """Visit only the argument's value, not the keyword it is passed as."""
        node.value.visit(self)
        return False


def names_read_by(node: cst.CSTNode) -> set[str]:
    """Return every name `node` reads, built-ins included; attribute names and keyword argument names are not reads."""
    collector = _NameCollector()
    node.visit(collector)
    return collector.names


def assigned_names(statement: cst.Assign | cst.AnnAssign) -> set[str]:
    """Return every name an assignment's targets use, including inside tuple or list targets."""
    targets = [target.target for target in statement.targets] if isinstance(statement, cst.Assign) else [statement.target]
    collector = _NameCollector()
    for target in targets:
        target.visit(collector)
    return collector.names

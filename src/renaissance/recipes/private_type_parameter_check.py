# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Recipe that drops the leading underscore from the names of PEP 695 type parameters."""

import keyword
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import libcst as cst

from renaissance.integrations.python.ast.cst_node import PythonCstNode
from renaissance.integrations.python.ast.factory import PythonFactory, PythonPattern, PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.utils.cst_utils import names_read_by

_TYPE_PARAM_NODES = (cst.TypeVar, cst.ParamSpec, cst.TypeVarTuple)
type _TypeParam = cst.TypeVar | cst.ParamSpec | cst.TypeVarTuple
type _Position = tuple[int, int]
type _Edit = tuple[PythonCstNode, str]

# TODO(FrancescoPezzella): these patterns do not find a class with two or more keyword arguments in its bases, nor a
#  function with default values, keyword-only or positional-only parameters.
#  https://github.com/TNO/Renaissance.Py/issues/279
_DECLARATION_PATTERNS = (
    "@$$decorators\ndef $f[$$tps]($$args, *$$varargs, **$$kwargs) -> $r:\n    $$body",
    "@$$decorators\ndef $f[$$tps]($$args, *$$varargs, **$$kwargs):\n    $$body",
    "@$$decorators\nclass $c[$$tps]($$bases):\n    $$body",
    "@$$decorators\nclass $c[$$tps]($$bases, $kw=$v):\n    $$body",
)


class _RenameNames(cst.CSTTransformer):
    """Rename the names an expression reads: every `Name` except an attribute's or a keyword argument's own name."""

    def __init__(self, renames: Mapping[str, str]) -> None:
        """Rename each key of renames to its value."""
        super().__init__()
        self.renames = renames

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:  # noqa: N802 - libcst dispatches on this name
        """Return the node with its new name if it has one."""
        return updated_node.with_changes(value=self.renames.get(original_node.value, original_node.value))

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.Attribute:  # noqa: N802 - libcst dispatches on this name
        """Keep the attribute's own name: in `np.T`, `T` is not a read of the name `T`."""
        return updated_node.with_changes(attr=original_node.attr)

    def leave_Arg(self, original_node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:  # noqa: N802 - libcst dispatches on this name
        """Keep the keyword argument's own name."""
        return updated_node.with_changes(keyword=original_node.keyword)


class _StringNames(cst.CSTVisitor):
    """Collect the names read by every string in a tree that parses as an expression, such as an annotation."""

    def __init__(self) -> None:
        """Start with no names collected."""
        super().__init__()
        self.names: set[str] = set()

    def visit_SimpleString(self, node: cst.SimpleString) -> None:  # noqa: N802 - libcst dispatches on this exact name
        """Record the names read by the string, if it parses as an expression."""
        try:
            self.names |= names_read_by(cst.parse_expression(node.raw_value))
        except cst.ParserSyntaxError:
            return


def _declared_name(param: PythonCstNode) -> str:
    """Return the name a type parameter declares."""
    return cast("_TypeParam", param.node).name.value


def _owner(param: PythonCstNode) -> PythonCstNode:
    """Return the function or class whose type parameters declare param."""
    owner = param.parent
    while owner is not None and not isinstance(owner.node, (cst.FunctionDef, cst.ClassDef)):
        owner = owner.parent
    if owner is None:
        message = f"The type parameter {_declared_name(param)} has no function or class around it."
        raise ValueError(message)
    return owner


def _renamed_string(string: cst.SimpleString, renames: Mapping[str, str]) -> str | None:
    """Return the source of string with the names in renames renamed inside it, or None if it holds no expression."""
    try:
        expression = cst.parse_expression(string.raw_value)
    except cst.ParserSyntaxError:
        return None
    renamed = cst.ensure_type(expression.visit(_RenameNames(renames)), cst.BaseExpression)
    inner = cst.Module([]).code_for_node(renamed)
    return f"{string.prefix}{string.quote}{inner}{string.quote}"


def _declared_positions(nodes: Sequence[PythonRstNode], patterns: Sequence[Sequence[PythonPattern]]) -> set[_Position]:
    """Return the (offset, length) of every type parameter that a function or class in nodes declares, nested ones included."""
    positions: set[_Position] = set()
    for pattern in patterns:
        for match in match_pattern(nodes, pattern):
            positions.update((param.offset, param.length) for param in match.expansions["$$tps"])
            positions |= _declared_positions(match.nodes[0].children, patterns)
    return positions


class PrivateTypeParameterCheck(PythonRefactoring[PythonCstNode]):
    """Rename PEP 695 type parameters such as `_T` to `T`, together with every use they bind.

    Patterns locate the declarations; libcst's scope analysis finds the uses, so a module-level `_T` of the same name
    is left alone. A type parameter is left unchanged when its new name is already taken in the declaring function or
    class, or is already a name there.
    """

    def __init__(self, file: Path) -> None:
        """Prepare the recipe for file, parsed with the CST backend."""
        super().__init__(file, PythonCstNode)

    def run(self) -> None:
        """Run check() and store its result on self.result."""
        self.result = self.check()

    def check(self) -> dict[str, str]:
        """Rename every private type parameter that can be renamed safely.

        Returns {old name: "fixed" | "unsafe"}; a name refused in any declaration is "unsafe".
        """
        results: dict[str, str] = {}
        for owner, params in self._private_type_params().items():
            edits = self._plan_renames(owner, params)
            status = "unsafe" if edits is None else "fixed"
            for param in params:
                name = _declared_name(param)
                results[name] = "unsafe" if "unsafe" in (status, results.get(name)) else status
            for target, text in edits or []:
                self.replace(text, target, include_whitespace=False, include_comments=False)
        return results

    def _private_type_params(self) -> dict[PythonCstNode, list[PythonCstNode]]:
        """Return the private type parameters of each function or class, found with patterns on a parse of the same text."""
        unit = cast("PythonCstNode", cast("object", self.root)).translation_unit
        rst_factory = PythonFactory(PythonRstNode)
        pattern_factory = PythonPatternFactory(rst_factory)
        patterns = [pattern_factory.create_statements(text) for text in _DECLARATION_PATTERNS]
        declared = _declared_positions([PythonRstNode.load_from_text(unit.content, unit.file_name)], patterns)
        by_position = {(node.offset, node.length): node for node in unit.wrappers.values() if isinstance(node.node, _TYPE_PARAM_NODES)}
        owners: dict[PythonCstNode, list[PythonCstNode]] = {}
        for position in sorted(declared):
            param = by_position[position]
            if _declared_name(param).startswith("_"):
                owners.setdefault(_owner(param), []).append(param)
        return owners

    def _plan_renames(self, owner: PythonCstNode, params: list[PythonCstNode]) -> list[_Edit] | None:
        """Return the edits that rename params, or None if a new name would clash or capture another one."""
        unit = owner.translation_unit
        renames = {_declared_name(param): _declared_name(param).lstrip("_") for param in params}
        if not all(new.isidentifier() and not keyword.iskeyword(new) for new in renames.values()):
            return None
        if self._clashes(owner, renames):
            return None
        edits: list[_Edit] = []
        string_uses: dict[PythonCstNode, dict[str, str]] = {}
        for param in params:
            old = _declared_name(param)
            edits.append((unit.wrappers[cast("_TypeParam", param.node).name], renames[old]))
            for reference in param.referenced_by:
                use = reference.node
                if isinstance(use.node, cst.Name):
                    edits.append((use, renames[old]))
                elif isinstance(use.node, cst.SimpleString):
                    string_uses.setdefault(use, {})[old] = renames[old]
                else:
                    return None
        for use, string_renames in string_uses.items():
            text = _renamed_string(cast("cst.SimpleString", use.node), string_renames)
            if text is None:
                return None
            edits.append((use, text))
        return edits

    @staticmethod
    def _clashes(owner: PythonCstNode, renames: Mapping[str, str]) -> bool:
        """Return whether a new name is declared twice in the bracket or already a name in the declaring function or class."""
        node = cast("cst.FunctionDef | cst.ClassDef", owner.node)
        declared = [type_param.param.name.value for type_param in node.type_parameters.params] if node.type_parameters else []
        final = [renames.get(name, name) for name in declared]
        strings = _StringNames()
        node.visit(strings)
        return len(set(final)) != len(final) or bool(set(renames.values()) & (names_read_by(node) | strings.names))

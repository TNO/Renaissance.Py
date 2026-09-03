import ast
import sys
import textwrap
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Self

from renaissance.integrations.python.ast.util import convert
from renaissance.integrations.types import *
from renaissance.syntax_tree.match_finder import find_in_list
from renaissance.utils.ast_utils import (
    format_node,
    match_children,
    match_props,
    next_sibling,
    preceding_sibling,
    traverse,
)

types = ["int", "float", "str", "list", "set", "tuple", "Mapping", "dict", "Optional"]
IRRELEVANT_PROPS = {"comment"}
IRRELEVANT_NODES = {"comment"}
IMPLICIT = [ImplicitNode]


class ImplicitNode(ast.Name):
    _fields = (
        "id",
        "body",
    )

    _field_types = {
        "id": str,
        "body": list,
    }

    def __init__(self, name, children=None):
        super().__init__(name)
        self.body = children or []
        self.lineno = 0
        self.col_offset = 0
        self.end_lineno = 0
        self.end_col_offset = 0


class PythonRSTReference:
    def __repr__(self):
        return f"{self.node_id}:{self.ref_kind}"

    def __init__(self, node_id: str, ref_kind: str, properties: dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties


class PythonRstTranslationUnit:
    cache = {}

    def __init__(self, content, file_name: str):
        self.content = content.encode(sys.getfilesystemencoding())
        self.atu = ast.parse(content, file_name)
        self.file_name = file_name
        self.references_initialized = False
        PythonRstTranslationUnit.cache[file_name] = content
        self.lines = self.content.splitlines()

        self._references: dict[str, list[PythonRSTReference]] = {}
        self._referenced_by: dict[str, list[PythonRSTReference]] = {}
        self._nodes: dict[str, PythonRstNode] = {}

    def check_diagnostics(self, continue_with_warning=True) -> None:
        msg = None
        errors = ""
        for d in self.atu.type_ignores:
            msg = f"type ignored: {d.tag} at {d.lineno}\n"
            errors += msg
            print(msg)
        if msg and not continue_with_warning:
            raise Exception(f"Error parsing: {self.file_name} \n+ errors: {errors}")

    def lazy_create_refers(self, node: PythonRstNode) -> None:
        if self.references_initialized:
            return
        for n in traverse(node.root):
            self.create_references(n)
        self.references_initialized = True

    def add(self, node):
        match node.ast_type.__name__:
            case "Name":
                if node.node.id not in self._nodes and node.node.id not in types:
                    self._nodes[node.node.id] = node
            case "FunctionDef":
                if node.node.name not in self._nodes:
                    self._nodes[node.node.name] = node
            case "Call":
                if node.name not in self._nodes:
                    self._nodes[node.name] = node
            case "ClassDef":
                if node.name not in self._nodes:
                    self._nodes[node.name] = node
            case "arg":
                if node.name != "self":
                    if node.name not in self._nodes:
                        self._nodes[node.name] = node

    def create_references(self, ast_node) -> None:
        assert isinstance(ast_node, PythonRstNode), f"Expected PythonASTNode but got {type(ast_node)}"
        match type(ast_node.node):
            case ast.arg:
                if ast_node.name != "self":
                    if isinstance(ast_node.node, ast.arg) and isinstance(ast_node.node.annotation, ast.Name):
                        node_id = ast_node.name
                        ref_id = ast_node.node.annotation.id
                        ref_kind = "TypeRef"
                        self.add_reference(node_id, ref_id, ref_kind)
            case ast.Assign:
                if isinstance(ast_node.node, ast.Assign):
                    for n in ast_node.node.targets:
                        if isinstance(n, ast.Name) and isinstance(ast_node.node.value, ast.Call):
                            node_id = n.id
                            func = ast_node.node.value.func
                            ref_id = func.id if isinstance(func, ast.Name) else None
                            if ref_id:
                                ref_kind = "CallRef"
                                self.add_reference(node_id, ref_id, ref_kind)
            case ast.AnnAssign:
                if isinstance(ast_node.node, ast.AnnAssign):
                    if (
                        ast_node.node.annotation
                        and isinstance(ast_node.node.target, ast.Name)
                        and isinstance(ast_node.node.annotation, ast.Name)
                    ):
                        node_id = ast_node.node.target.id
                        ref_id = ast_node.node.annotation.id
                        ref_kind = "TypeRef"
                        self.add_reference(node_id, ref_id, ref_kind)
            case ast.ClassDef:
                if isinstance(ast_node.node, ast.ClassDef):
                    node = ast_node.node
                    node_id = node.name
                    if node.bases:
                        ref_node = node.bases[0]
                        if isinstance(ref_node, ast.Name):
                            ref_id = ref_node.id
                            ref_kind = "Inherit"
                            self.add_reference(node_id, ref_id, ref_kind)
                # add functions and attributes to class

            case ast.Call:
                if isinstance(ast_node.node, ast.Call):
                    # obj.function. then obj refers to function
                    if isinstance(ast_node.node.func, ast.Attribute):
                        node_id = ast_node.name
                        ref_id = ast_node.node.func.attr
                        ref_kind = "FuncCall"
                        self.add_reference(node_id, ref_id, ref_kind)
                    # call function 'a' in function 'b', then 'b' refers to 'a'
                    container = ast_node.get_container_parent()
                    if container.ast_type == FunctionDef and isinstance(ast_node.node.func, ast.Name):
                        node_id = container.name
                        ref_id = ast_node.node.func.id
                        ref_kind = "FuncCall"
                        self.add_reference(node_id, ref_id, ref_kind)

    def add_reference(self, node_id: str, ref_id: str, ref_kind: str) -> None:
        properties = {}
        if node_id == ref_id:
            return
        reference = PythonRSTReference(ref_id, ref_kind, properties)
        referenced_by = PythonRSTReference(node_id, ref_kind, properties)
        if node_id in self._references:
            self._references[node_id].append(reference)
        else:
            self._references[node_id] = [reference]
        if ref_id in self._referenced_by:
            self._referenced_by[ref_id].append(referenced_by)
        else:
            self._referenced_by[ref_id] = [referenced_by]

    def get_referenced_by(self, node_id):
        refs = self._referenced_by.get(node_id, [])
        return [PythonRSTReference(self._nodes[ref.node_id].name, ref.ref_kind, ref.properties) for ref in refs]

    def get_references(self, node_id):
        refs = self._references.get(node_id, [])
        return [PythonRSTReference(self._nodes[ref.node_id].name, ref.ref_kind, ref.properties) for ref in refs]


class PythonRstNode:
    def __init__(self, node: ast.AST, translation_unit: PythonRstTranslationUnit = None, parent=None):
        self.root = parent.root if parent and parent.root else self
        self.node = node
        self.parent = parent
        self.translation_unit: PythonRstTranslationUnit = translation_unit
        self.ast_type = KIND_MAP.get(type(node).__name__, UnknownType)
        if self.ast_type == UnknownType:
            print(f'"{type(node).__name__}": {type(node).__name__},')

        self.indent = ""
        self.name = self._derive_name()
        self.show_props = False
        self.children = []
        self.properties = {}
        self.is_implicit = self.ast_type not in IMPLICIT
        self.offset = 0
        self.length = 0
        if self.translation_unit:
            self.filename = translation_unit.file_name
            self.derive_position(node, translation_unit, parent)
            self.add_node()
        for name in node._fields:
            try:
                child = getattr(node, name)
                match child:
                    case list():  # Matches any list
                        if isinstance(node, Global) and name == "names":
                            if len(child) == 1:
                                self.name = child[0]
                            if name == "body":
                                self.body = self.children

                        if isinstance(node, ImplicitNode) or isinstance(node, ast.Module) or len(node._fields) == 1:
                            self.children.extend(PythonRstNode(n, translation_unit, self) for n in child)
                            if name == "body":
                                self.body = self.children
                        else:
                            self.children.append(PythonRstNode(ImplicitNode(name, child), translation_unit, self))
                            if name in ["body", "cases"]:
                                self.body = self.children[-1].children

                    case ast.AST():
                        if name not in ["ctx"]:
                            self.children.append(PythonRstNode(child, translation_unit, self))
                            if isinstance(child, ast.expr):
                                self.expression = self.children[-1]
                    case _:
                        if name not in ["None"]:
                            self.properties[name] = child
            except AttributeError as e:
                print(e)
                continue

        self.end_offset = self.offset + self.length
        self.extended_end_offset = self.end_offset
        self.is_statement = isinstance(self.node, ast.stmt)

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self.ast_type == other.ast_type
            and match_props(self.properties, other.properties, IRRELEVANT_PROPS)
            and match_children(self.children, other.children, IRRELEVANT_NODES)
        )

    def __contains__(self, item):
        if not isinstance(item, list):
            item = [item]
        return find_in_list(self.children, item)

    def __getitem__(self, key):
        """Allow indexing/slicing into node to access children.

        Usage: node[0] == node.children[0]
        """
        return self.children[key]

    def __repr__(self):
        return format_node(self)

    @property
    def next_sibling(self) -> Self | None:
        return next_sibling(self)

    @property
    def preceding_sibling(self) -> Self | None:
        return preceding_sibling(self)

    def process(self, function: Callable[[Self], None]) -> None:
        function(self)
        for child in self.children:
            child.process(function)

    def derive_position(self, node: ast.AST, translation_unit: PythonRstTranslationUnit, parent):
        if node._attributes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.decorator_list:
                self.offset = convert(self.translation_unit.lines, node.decorator_list[0].lineno, node.decorator_list[0].col_offset) - 1
            elif parent.name == "decorator_list":
                # also include the @ in the decorator
                self.offset = convert(self.translation_unit.lines, node.lineno, node.col_offset) - 1  # type: ignore[attr-defined]
            else:
                self.offset = convert(self.translation_unit.lines, node.lineno, node.col_offset)  # type: ignore[attr-defined]
            all_space = all(c == " " for c in self.translation_unit.content[self.offset - node.col_offset : self.offset])
            if all_space:
                self.offset = max(self.offset - node.col_offset, 0)
            self.length = convert(self.translation_unit.lines, node.end_lineno, node.end_col_offset) - self.offset  # type: ignore[attr-defined]
        elif isinstance(node, ast.Module) and translation_unit:
            self.offset = 0
            self.length = len(translation_unit.content)
        else:
            self.offset = 0
            self.length = 0

    @staticmethod
    def load(
        file_path: Path,  # TODO: why Path - why not FileDescriptorOrPath (the type of the file parameter of the open function)?
        extra_args: Sequence[str] | None = None,
        working_dir: Path | None = None,
    ) -> PythonRstNode:
        # Keep a uniform loader signature across AST node implementations.
        # Python's AST parser does not need extra arguments or a working dir.
        _ = extra_args, working_dir
        with open(file_path) as file:
            content = file.read()
            return PythonRstNode.load_from_text(content, str(file_path))

    @staticmethod
    def load_from_text(
        text: str,
        file_name: str = "test.py",
        extra_args: Sequence[str] | None = None,
        working_dir: Path | None = None,
    ) -> PythonRstNode:
        _ = extra_args, working_dir
        translation_unit = PythonRstTranslationUnit(text, file_name=str(file_name))
        translation_unit.check_diagnostics()
        root_node = PythonRstNode(translation_unit.atu, translation_unit)
        return root_node

    def _derive_name(self):

        if (
            isinstance(
                self.node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.ExceptHandler,
                ),
            )
            and self.node.name
        ):
            name = self.node.name
        elif isinstance(self.node, ast.Global) and len(self.node.names) == 1:
            name = self.node.names[0]
        elif isinstance(self.node, (ast.AnnAssign, ast.AugAssign)) and isinstance(self.node.target, ast.Name):
            name = self.node.target.id
        elif isinstance(self.node, ast.Assign) and len(self.node.targets) == 1:
            target = self.node.targets[0]
            if isinstance(target, ast.Name):
                name = target.id
            else:
                name = self.ast_type.__name__
        elif isinstance(self.node, ast.Name):
            name = self.node.id
        elif isinstance(self.node, ast.arg):
            name = self.node.arg
        elif isinstance(self.node, ast.Match) and isinstance(self.node.subject, ast.Name):
            name = self.node.subject.id
        elif (isinstance(self.node, ast.Import) and len(self.node.names) == 1) or (
            isinstance(self.node, ast.ImportFrom) and len(self.node.names) == 1
        ):
            name = self.node.names[0].name
        elif isinstance(self.node, (ast.Assert, ast.Break, ast.Pass, ast.Raise, ast.Continue)):
            name = ""
        elif isinstance(self.node, (ast.For, ast.AsyncFor)):
            if isinstance(self.node.target, Tuple):
                name = self.node.target.dims[1].id
            elif isinstance(self.node.target, ast.Name):
                name = self.node.target.id
            else:
                name = str(self.node.target)
        elif "body" not in self.node._fields:
            name = ast.unparse(self.node)
        elif isinstance(self.node, (ast.Module)) and self.translation_unit:
            name = self.translation_unit.file_name
        else:
            name = self.ast_type.__name__
        return name or ""

    @property
    def type(self):
        return self.node.annotation.id if isinstance(self.node, ast.AnnAssign) and isinstance(self.node.annotation, ast.Name) else None

    @property
    def value(self):
        if self.ast_type == Assert:
            return 0
        return self.node.value.value if hasattr(self.node, "value") else None

    @property
    def expr(self):
        if (
            isinstance(
                self.node,
                (
                    ast.Assign,
                    ast.AnnAssign,
                    ast.AugAssign,
                    ast.Return,
                    ast.Expr,
                    ast.Delete,
                    ast.NamedExpr,
                ),
            )
            and hasattr(self.node, "value")
            and self.node.value is not None
        ) or (isinstance(self.node, ast.Expr) and hasattr(self.node, "value")):
            return PythonRstNode(self.node.value, self.translation_unit, self)
        if isinstance(self.node, (ast.For, ast.AsyncFor, ast.comprehension)):
            return PythonRstNode(self.node.iter, self.translation_unit, self)
        if isinstance(self.node, (ast.If, ast.While, ast.Assert)):
            return PythonRstNode(self.node.test, self.translation_unit, self)
        if isinstance(self.node, (ast.Raise, ast.ExceptHandler)) and hasattr(self.node, "exc") and self.node.exc is not None:
            return PythonRstNode(self.node.exc, self.translation_unit, self)
        return None

    @property
    def operator(self):
        node_type = type(self.node).__name__
        op = type(self.node.op).__name__ if isinstance(self.node, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.AugAssign)) else ""
        return OPERATOR_MAP.get(node_type + op, "")

    @property
    def signature(self) -> str:
        sig = self.binary_file_content().decode(sys.getfilesystemencoding())
        if self.parent and self.parent.name == "decorator_list" and not sig.startswith("@"):
            sig = "@" + sig
        return sig

    def binary_file_content(self) -> bytes:
        return (
            self.translation_unit.content[self.offset : self.offset + self.length]
            if self.translation_unit
            else ast.unparse(self.node).encode(sys.getfilesystemencoding())
        )

    @property
    def referenced_by(self) -> Sequence[PythonRSTReference]:
        self.translation_unit.lazy_create_refers(self)
        return self.translation_unit.get_referenced_by(self.name)

    @property
    def references(self) -> list[PythonRSTReference]:
        self.translation_unit.lazy_create_refers(self)
        return self.translation_unit.get_references(self.name)

    def add_node(self):
        self.translation_unit.add(self)

    def get_container_parent(self):
        if self.parent:
            if self.parent.ast_type.__name__ in ["FunctionDef", "ClassDef", "Module"]:
                return self.parent
            return self.parent.get_container_parent()
        return self

    @property
    def text(self) -> str:
        return textwrap.dedent(self.signature)

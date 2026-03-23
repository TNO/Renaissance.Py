from pathlib import Path
from typing import Any, Optional, Sequence

from ast_comments import *
from typing_extensions import override

from renaissance.impl import MATCH_ONE, MATCH_ALL
from renaissance.syntax_tree import ASTNode, ASTReference
from renaissance.syntax_tree.match_finder import find_in_list

OPERATOR_MAP = {
    "AnnAssign": "=",
    "Assert": "assert",
    "Assign": "=",
    "AsyncFor": "for",
    "AsyncFunctionDef": "function",
    "AsyncWith": "with",
    "AugAssignAdd": "+=",
    "Break": "break",
    "Call": "def",
    "ClassDef": "class",
    "Continue": "continue",
    "For": "for",
    "FunctionDef": "function",
    "If": "if",
    "Import": "import",
    "ImportFrom": "import",
    "Match": "match",
    "Pass": "pass",
    "Try": "try",
    "TryStar": "try",
    "While": "while",
    "With": "with",
}
types = ["int", "float", "str", "list", "set", "tuple", "Mapping", "dict", "Optional"]
IRRELEVANT_PROPS = {"comment"}


class PythonASTReference:
    def __repr__(self):
        return f"{self.node_id}:{self.ref_kind}"

    def __init__(self, node_id: str, ref_kind: str, properties: dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties


class PythonTranslationUnit:
    cache = {}

    def __init__(self, content, file_name: str):
        self.content = content.encode(sys.getfilesystemencoding())
        self.atu = parse(content, file_name, type_comments=True)
        self.file_name = file_name
        self.references_initialized = False
        PythonTranslationUnit.cache[file_name] = content
        self.lines = self.content.splitlines()

        self._references: dict[str, list[PythonASTReference]] = {}
        self._referenced_by: dict[str, list[PythonASTReference]] = {}
        self._nodes: dict[str, "PythonASTNode"] = {}

    def check_diagnostics(self, continue_with_warning=True) -> None:
        msg = None
        errors = ""
        for d in self.atu.type_ignores:
            msg = f"type ignored: {d.tag} at {d.lineno}\n"
            errors += msg
            print(msg)
        if msg and not continue_with_warning:
            raise Exception(f"Error parsing: {self.file_name} \n+ errors: {errors}")

    def lazy_create_refers(self, node: "ASTNode") -> None:
        if self.references_initialized:
            return
        node.root.process(lambda n: self.create_references(n))
        self.references_initialized = True

    def convert(self, line_nr, col):
        if line_nr > len(self.lines):
            return 0
        return sum(len(self.lines[i]) + 1 for i in range(line_nr - 1)) + col
        # add node to the node list for references

    def add(self, node):
        match node.kind:
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
        assert isinstance(ast_node, PythonASTNode), f"Expected PythonASTNode but got {type(ast_node)}"
        match ast_node.kind:
            case "arg":
                if ast_node.name != "self":
                    if isinstance(ast_node.node, ast.arg) and isinstance(ast_node.node.annotation, ast.Name):
                        node_id = ast_node.name
                        ref_id = ast_node.node.annotation.id
                        ref_kind = "TypeRef"
                        self.add_reference(node_id, ref_id, ref_kind)
            case "Assign":
                if isinstance(ast_node.node, ast.Assign):
                    for n in ast_node.node.targets:
                        if isinstance(n, ast.Name) and isinstance(ast_node.node.value, ast.Call):
                            node_id = n.id
                            func = ast_node.node.value.func
                            ref_id = func.id if isinstance(func, ast.Name) else None
                            if ref_id:
                                ref_kind = "CallRef"
                                self.add_reference(node_id, ref_id, ref_kind)
            case "AnnAssign":
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
            case "ClassDef":
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

            case "Call":
                if isinstance(ast_node.node, ast.Call):
                    # obj.function. then obj refers to function
                    if isinstance(ast_node.node.func, ast.Attribute):
                        node_id = ast_node.name
                        ref_id = ast_node.node.func.attr
                        ref_kind = "FuncCall"
                        self.add_reference(node_id, ref_id, ref_kind)
                    # call function 'a' in function 'b', then 'b' refers to 'a'
                    container = ast_node.get_container_parent()
                    if container.kind == "FunctionDef" and isinstance(ast_node.node.func, ast.Name):
                        node_id = container.name
                        ref_id = ast_node.node.func.id
                        ref_kind = "FuncCall"
                        self.add_reference(node_id, ref_id, ref_kind)

    def add_reference(self, node_id: str, ref_id: str, ref_kind: str) -> None:
        properties = {}
        if node_id == ref_id:
            return
        reference = PythonASTReference(ref_id, ref_kind, properties)
        referenced_by = PythonASTReference(node_id, ref_kind, properties)
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
        return [ASTReference(self._nodes[ref.node_id], ref.ref_kind, ref.properties) for ref in refs]

    def get_references(self, node_id):
        refs = self._references.get(node_id, [])
        return [ASTReference(self._nodes[ref.node_id], ref.ref_kind, ref.properties) for ref in refs]


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


class PythonASTNode(ASTNode):
    def __init__(self, node: ast.AST, translation_unit: PythonTranslationUnit = None, parent=None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._parent = parent
        self._kind = self.derive_kind()
        self.indent = ""
        self._name = self._derive_name()
        self.show_props = False
        self._children = []
        self._properties = {}
        if translation_unit:
            self._filename = translation_unit.file_name
            self.translation_unit = translation_unit
            self.derive_position(node, translation_unit, parent)
            self.add_node()
        else:
            self._filename = ""
            self._length = 0
            self._offset = 0
            self.translation_unit = None

        for name in node._fields:
            try:
                child = getattr(node, name)
                match child:
                    case list():  # Matches any list
                        if isinstance(node, ImplicitNode) or isinstance(node, ast.Module) or len(node._fields) == 1:
                            self._children.extend(PythonASTNode(n, translation_unit, self) for n in child)
                            if name == "body":
                                self.body = self._children
                        else:
                            self._children.append(PythonASTNode(ImplicitNode(name, child), translation_unit, self))
                            if name in ["body", "cases"]:
                                self.body = self._children[-1].children
                    case ast.AST():
                        if name not in ["ctx"]:
                            self._children.append(PythonASTNode(child, translation_unit, self))
                            if isinstance(child, ast.expr):
                                self.expression = self.children[-1]
                    case _:
                        if name not in ["None"]:
                            self.properties[name] = child
            except AttributeError as e:
                print(e)
                continue

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self.kind == other.kind
            and self.match_props(other.properties)
            and self.match_children(other.children)
        )

    def __contains__(self, item):
        if isinstance(item, self.__class__):
            item = [item]
        return find_in_list(self.children, item)

    def __getitem__(self, key):
        """Allow indexing/slicing into node to access children.

        Usage: node[0] == node.children[0]
        """
        return self.children[key]

    def derive_kind(self) -> str:
        signature = ""
        if isinstance(self.node, ast.arg):
            signature = self.node.arg
        elif isinstance(self.node, ast.Name):
            signature = self.node.id
        elif isinstance(self.node, ast.Expr) and isinstance(self.node.value, ast.Name):
            signature = self.node.value.id
        if (
            (signature.startswith(MATCH_ALL) or signature.startswith("$$")) and " " not in signature and "(" not in signature
        ):  # legacy compatibility
            return MATCH_ALL
        elif (signature.startswith(MATCH_ONE) or signature.startswith("$")) and " " not in signature and "(" not in signature:
            return MATCH_ONE
        return type(self.node).__name__

    def match_props(self, properties) -> bool:
        all_keys = (self.properties.keys() | properties.keys()) - IRRELEVANT_PROPS
        return all(self.properties.get(n) == properties.get(n) for n in all_keys)

    def match_children(self, children):
        return all(self[i] == child for i, child in enumerate(children))

    def derive_position(self, node: ast.AST, translation_unit: PythonTranslationUnit, parent):
        if node._attributes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.decorator_list:
                self._offset = self.translation_unit.convert(node.decorator_list[0].lineno, node.decorator_list[0].col_offset) - 1
            elif parent.name == "decorator_list":
                # also include the @ in the decorator
                self._offset = self.translation_unit.convert(node.lineno, node.col_offset) - 1  # type: ignore[attr-defined]
            else:
                self._offset = self.translation_unit.convert(node.lineno, node.col_offset)  # type: ignore[attr-defined]
            self._length = self.translation_unit.convert(node.end_lineno, node.end_col_offset) - self.offset  # type: ignore[attr-defined]
        elif isinstance(node, ast.Module) and translation_unit:
            self._offset = 0
            self._length = len(translation_unit.content)
        else:
            self._offset = 0
            self._length = 0

    @override
    @staticmethod
    def load(file_path: Path, extra_args: Sequence[str], working_dir: Path) -> "PythonASTNode":
        with open(working_dir / file_path, "r") as file:
            content = file.read()
            return PythonASTNode.load_from_text(content, str(file_path), extra_args, working_dir)

    @override
    @staticmethod
    def load_from_text(
        text: str,
        file_name: str = "test.py",
        extra_args: Sequence[str] = None,
        working_dir: Path = None,
    ) -> "PythonASTNode":
        translation_unit = PythonTranslationUnit(text, file_name=str(file_name))
        translation_unit.check_diagnostics()
        root_node = PythonASTNode(translation_unit.atu, translation_unit, None)
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
                name = self.kind
        elif isinstance(self.node, ast.Name):
            name = self.node.id
        elif isinstance(self.node, ast.arg):
            name = self.node.arg
        elif isinstance(self.node, ast.Match) and isinstance(self.node.subject, ast.Name):
            name = self.node.subject.id
        elif isinstance(self.node, ast.Import) and len(self.node.names) == 1:
            name = self.node.names[0].name
        elif isinstance(self.node, ast.ImportFrom) and len(self.node.names) == 1:
            name = self.node.names[0].name
        elif isinstance(self.node, (ast.Assert, ast.Break, ast.Pass, ast.Raise, ast.Continue)):
            name = ""
        elif isinstance(self.node, (ast.For, ast.AsyncFor)):
            if isinstance(self.node.target, Tuple):
                name = getattr(self.node.target.dims[1], "id")
            elif isinstance(self.node.target, Name):
                name = self.node.target.id
            else:
                name = str(self.node.target)
        elif "body" not in self.node._fields:
            name = unparse(self.node)
        else:
            name = self.kind
        return name.replace(MATCH_ALL, "$$").replace(MATCH_ONE, "$")

    @property
    def type(self):
        return self.node.annotation.id if isinstance(self.node, ast.AnnAssign) and isinstance(self.node.annotation, ast.Name) else None

    @property
    def value(self):
        if self.kind == "Assert":
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
        ):
            return PythonASTNode(self.node.value, self.translation_unit, self)
        elif isinstance(self.node, ast.Expr) and hasattr(self.node, "value"):
            return PythonASTNode(self.node.value, self.translation_unit, self)
        elif isinstance(self.node, (ast.For, ast.AsyncFor, ast.comprehension)):
            return PythonASTNode(self.node.iter, self.translation_unit, self)
        elif isinstance(self.node, (ast.If, ast.While, ast.Assert)):
            return PythonASTNode(self.node.test, self.translation_unit, self)
        elif isinstance(self.node, (ast.Raise, ast.ExceptHandler)) and hasattr(self.node, "exc") and self.node.exc is not None:
            return PythonASTNode(self.node.exc, self.translation_unit, self)
        else:
            return None

    @property
    def operator(self):
        node_type = type(self.node).__name__
        op = type(self.node.op).__name__ if isinstance(self.node, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.AugAssign)) else ""
        return OPERATOR_MAP.get(node_type + op, "")

    @override
    @property
    def signature(self) -> str:
        sig = self.binary_file_content().decode(sys.getfilesystemencoding())
        if self.parent and self.parent.name == "decorator_list" and not sig.startswith("@"):
            sig = "@" + sig
        return sig

    @override
    def binary_file_content(self, file_path: str | None = None) -> bytes:
        return (
            self.translation_unit.content[self.offset : self.end_offset]
            if self.translation_unit
            else unparse(self.node).encode(sys.getfilesystemencoding())
        )

    @override
    def matches_kind(self, target: ASTNode) -> bool:
        return isinstance(self.node, type(target.node))

    @override
    @property
    def parent(self) -> Optional["PythonASTNode"]:
        return self._parent

    @property
    @override
    def is_statement(self) -> bool:
        return isinstance(self.node, ast.stmt)

    @override
    @property
    def referenced_by(self) -> Sequence[ASTReference]:
        self.translation_unit.lazy_create_refers(self)
        return self.translation_unit.get_referenced_by(self.name)

    @override
    @property
    def references(self) -> list[ASTReference]:
        self.translation_unit.lazy_create_refers(self)
        return self.translation_unit.get_references(self.name)

    @property
    @override
    def extended_end_offset(self) -> int:
        return self.offset + self.length

    def add_node(self):
        self.translation_unit.add(self)

    def get_container_parent(self):
        # Get the containing definition parent
        if self.parent and self.parent.kind == "FunctionDef":
            return self.parent
        elif self.parent and self.parent.kind == "ClassDef":
            return self.parent
        elif self.parent and self.parent.kind == "Module":
            return self.parent
        else:
            return self.parent.get_container_parent()

    @property
    def is_implicit(self):
        return self.is_part_of_translation_unit() and self.kind not in IMPLICIT


IMPLICIT = ["ImplicitNode"]

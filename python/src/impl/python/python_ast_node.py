import ast
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

from typing_extensions import override

from common import Stream
from impl import MATCH_ONE, MATCH_ALL
from syntax_tree import ASTNode, ASTReference
from syntax_tree.match_finder import is_match_dict, is_match_tree, match_pattern

EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []


class PythonASTReference:
    def __repr__(self):
        return f"{self.node_id}:{self.ref_kind}"

    def __init__(self, node_id: str, ref_kind: str, properties: dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties


class PythonTranslationUnit():
    cache = {}

    def __init__(self, content, file_name: str):
        self.content = content.encode(sys.getfilesystemencoding())
        self.atu = ast.parse(content, file_name)
        self.file_name = file_name
        self.references_initialized = False
        PythonTranslationUnit.cache[file_name] = content
        self.lines = self.content.splitlines()

        self._references: dict[str, list[PythonASTReference]] = {}
        self._referenced_by: dict[str, list[PythonASTReference]] = {}
        self._nodes: dict[str, 'PythonASTNode'] = {}

    def check_diagnostics(self) -> None:
        msg = None
        errors = ''
        for d in self.atu.type_ignores:
            msg = f'type ignored: {d.tag} at {d.lineno}\n'
            errors += msg
            print(msg)
        if msg:
            raise Exception(f'Error parsing: {self.file_name} \n+ errors: {errors}')

    def lazy_create_refers(self, node: 'ASTNode') -> None:
        if self.references_initialized:
            return
        node.root.process(ReferenceHelper.create_references)
        self.references_initialized = True

    def convert(self, line_nr, col):
        if (line_nr > len(self.lines)):
            return 0
        return sum(len(self.lines[i]) + 1 for i in range(line_nr - 1)) + col


class ImplicitNode(ast.Name):
    def __init__(self, name, children):
        super().__init__(name)
        self.body = children
        self.lineno = 0
        self.col_offset = 0
        self.end_lineno = 0
        self.end_col_offset = 0

    _fields = (
        'id',
        'body',
    )


class PythonASTNode(ASTNode):
    def __init__(self, node: ast.AST, translation_unit: PythonTranslationUnit = None, parent=None,
                 start_offset: Optional[int] = None, length: Optional[int] = None, insert_kind: Optional[str] = None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._parent = parent
        cls = type(node)
        self._kind = cls.__name__
        self.indent = ''
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
            self._filename = ''
            self._length = 0
            self._offset = 0
            self.translation_unit = None

        if isinstance(node, str):
            self._kind = 'Name'
            return

        node_id = self.derive_id(node)

        if node_id.startswith(MATCH_ONE):
            self._kind = MATCH_ONE
        elif node_id.startswith(MATCH_ALL):
            self._kind = MATCH_ALL

        for name in node._fields:
            try:
                child = getattr(node, name)
                match child:
                    case list():  # Matches any list
                        if isinstance(node, ImplicitNode) or isinstance(node, ast.Module) or len(node._fields) == 1:
                            self._children.extend(PythonASTNode(n, translation_unit, self) for n in child)
                            if name == 'body':
                                self.body = self._children
                        else:
                            self._children.append(PythonASTNode(ImplicitNode(name, child), translation_unit, self))
                            if name == 'body':
                                self.body = self._children[-1]
                    case ast.AST():
                        if name not in ['ctx']:
                            self._children.append(PythonASTNode(child, translation_unit, self))
                            if isinstance(child, ast.expr):
                                self.expression = self.children[-1]
                    case _:
                        if name not in ['None']:
                            self.properties[name] = child
            except AttributeError as e:
                print(e)
                continue

    def derive_id(self, node: ast.AST) -> str:
        result = ''
        if isinstance(node, ast.arg):
            result = node.arg
        elif isinstance(node, ast.Name):
            result = node.id
        elif (isinstance(node, ast.Expr) and isinstance(node.value, ast.Name)):
            result = node.value.id
        return result

    def __eq__(self, other: ASTNode):
        if (not other
                or not isinstance(other, type(self))
                # or len(self.children) != len(other.children)
                or self.kind != other.kind):
            return False
        return (is_match_dict(self.properties, other.properties, {})
                and is_match_tree(self.children, other.children, {}))

    def __contains__(self, item):
        return match_pattern([self], [item], {})

    def derive_position(self, node: ast.AST, translation_unit: PythonTranslationUnit, parent):
        if node._attributes:
            if parent.name == 'decorator_list':
                # also include the @ in the decorator
                self._offset = self.translation_unit.convert(self.node.lineno, self.node.col_offset) -1
            else:
                self._offset = self.translation_unit.convert(self.node.lineno, self.node.col_offset)
            self._length = self.translation_unit.convert(self.node.end_lineno, self.node.end_col_offset) - self.offset
        elif isinstance(node, ast.Module) and translation_unit:
            self._offset = 0
            self._length = len(translation_unit.content)
        else:
            self._offset = 0
            self._length = 0
        # If the source contains a decorator marker '@' immediately before the node,
        # include it in the signature so decorator nodes show the leading '@'.
        try:
            if self.translation_unit and self._offset > 0:
                # translation_unit.content is bytes
                if self.translation_unit.content[self._offset - 1:self._offset] == b'@':
                    self._offset -= 1
                    self._length += 1
        except Exception:
            pass

    @override
    @staticmethod
    def load(file_path: Path, extra_args: Sequence[str], working_dir: Path) -> 'PythonASTNode':
        with open(working_dir / file_path, 'r') as file:
            content = file.read()
            return PythonASTNode.load_from_text(content, file_path, extra_args, working_dir)

    @override
    @staticmethod
    def load_from_text(text: str, file_name: str, extra_args: Sequence[str], working_dir: Path) -> "PythonASTNode":
        translation_unit = PythonTranslationUnit(text, file_name=str(file_name))
        translation_unit.check_diagnostics()
        root_node = PythonASTNode(translation_unit.atu, translation_unit, None)
        return root_node

    @override
    def _derive_name(self):
        if isinstance(self.node, str):
            name = self.node
        elif 'body' not in self.node._fields:
            name = ast.unparse(self.node)
        elif 'name' in self.node._fields and self.node.name:
            name = self.node.name
        elif 'id' in self.node._fields and self.node.id:
            name = self.node.id
        else:
            name = self.kind
        return name.replace(MATCH_ALL, '$$').replace(MATCH_ONE, '$')

    @override
    @property
    def signature(self) -> str:
        sig = self.binary_file_content().decode(sys.getfilesystemencoding())
        if self.parent and self.parent.name == 'decorator_list' and not sig.startswith('@'):
            sig = '@'+sig
        return sig
    @override
    def binary_file_content(self, file_path: str | None = None) -> bytes:
        if self.translation_unit:
            txt = self.translation_unit.content[self.offset:self.end_offset]
        else:
            txt = ast.unparse(self.node).encode(sys.getfilesystemencoding())
            if type(self.node) is ast.Attribute:
                txt = '@' + txt
        return txt

    @override
    def matches_kind(self, target: ASTNode) -> bool:
        return isinstance(self.node, type(target.node))

    @override
    @property
    def parent(self) -> Optional['PythonASTNode']:
        return self._parent

    @override
    def is_statement(self) -> bool:
        return isinstance(self.node, ast.stmt)

    @override
    @property
    def referenced_by(self) -> Sequence[ASTReference]:
        # if both the function declaration and function definition are available node.name if hasattr(self.node, 'name') else self.node.id
        self.translation_unit.lazy_create_refers(self)
        node_id = self.node.name if hasattr(self.node, 'name') else self.node.id
        ref_by = self.translation_unit._referenced_by.get(node_id, EMPTY_LIST)
        # if both the function declaration and function definition are avaible 
        # the references are stored in the function definition
        # but we want them to also show up in the declaration
        if len(ref_by) == 0:
            definition = self._get_function_definition()
            if definition:
                ref_by = self.translation_unit._referenced_by.get(node_id, EMPTY_LIST)
        return Stream(ref_by) \
            .map(
            lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    def _get_function_definition(self):
        return None

    @property
    @override
    def extended_end_offset(self) -> int:
        return self.offset + self.length

    @override
    @property
    def references(self) -> Sequence[ASTReference]:
        self.translation_unit.lazy_create_refers(self)
        node_id = ''
        match self.kind:
            case 'FunctionDef':
                node_id = self.name
            case 'Call':
                node_id = self.name
            case 'ClassDef':
                node_id = self.name
            case 'Name':
                node_id = self.name
            case 'arg':
                node_id = self.name
        return Stream(self.translation_unit._references.get(node_id, EMPTY_LIST)) \
            .map(
            lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    def add_node(self):
        # add node to the node list for references
        match self.kind:
            case 'Name':
                if self.node.id not in self.translation_unit._nodes and self.node.id not in types:
                    self.translation_unit._nodes[self.node.id] = self
            case 'FunctionDef':
                if self.node.name not in self.translation_unit._nodes:
                    self.translation_unit._nodes[self.node.name] = self
            case 'Call':
                if self.name not in self.translation_unit._nodes:
                    self.translation_unit._nodes[self.name] = self
            case 'ClassDef':
                if self.name not in self.translation_unit._nodes:
                    self.translation_unit._nodes[self.name] = self
            case 'arg':
                if self.name != 'self':
                    if self.name not in self.translation_unit._nodes:
                        self.translation_unit._nodes[self.name] = self

    def get_container_parent(self):
        # Get the containing definition parent
        if self.parent and self.parent.kind == 'FunctionDef':
            return self.parent
        elif self.parent and self.parent.kind == 'ClassDef':
            return self.parent
        elif self.parent and self.parent.kind == 'Module':
            return self.parent
        else:
            return self.parent.get_container_parent()

    def __getitem__(self, key):
        """Allow indexing/slicing into node to access children.

        Usage: node[0] == node.children[0]
        """
        # support integer index and slice
        if isinstance(key, int):
            return self.children[key]
        if isinstance(key, slice):
            return self.children[key]
        # support string keys to access properties (e.g., node['name'])
        if isinstance(key, str):
            # be tolerant and return None if property missing
            return self.properties.get(key)
        raise TypeError(f"Indices must be integers or slices, not {type(key)}")


class ReferenceHelper:
    @staticmethod
    def create_references(ast_node: PythonASTNode) -> None:
        assert isinstance(ast_node, PythonASTNode), f'Expected PythonASTNode but got {type(ast_node)}'
        try:
            match ast_node.kind:
                case 'arg':
                    if ast_node.name != 'self':
                        if hasattr(ast_node.node, 'arg') and hasattr(ast_node.node, 'annotation'):
                            node_id = ast_node.name
                            ref_id = ast_node.node.annotation.id
                            ref_kind = 'TypeRef'
                            ReferenceHelper.add_reference(ast_node, node_id, ref_id, ref_kind)
                case 'Assign':
                    for n in ast_node.node.targets:
                        if isinstance(n, ast.Name) and isinstance(ast_node.node.value, ast.Call):
                            node_id = n.id
                            ref_id = ast_node.node.value.func.id
                            ref_kind = 'CallRef'
                            ReferenceHelper.add_reference(ast_node, node_id, ref_id, ref_kind)
                case 'AnnAssign':
                    if ast_node.node.annotation:
                        node_id = ast_node.node.target.id
                        ref_id = ast_node.node.annotation.id
                        ref_kind = 'TypeRef'
                    ReferenceHelper.add_reference(ast_node, node_id, ref_id, ref_kind)
                case 'ClassDef':
                    node = ast_node.node
                    node_id = ast_node.node.name
                    if node.bases:
                        ref_node = node.bases[0]
                        ref_id = ref_node.id
                        ref_kind = 'Inherit'
                        ReferenceHelper.add_reference(ast_node, node_id, ref_id, ref_kind)
                    # add functions and attributes to class

                case 'Call':
                    # obj.function. then obj refers to function
                    if hasattr(ast_node.node, 'func') and hasattr(ast_node.node.func, 'attr'):
                        node_id = ast_node.name
                        ref_id = ast_node.node.func.attr
                        ref_kind = 'FuncCall'
                        ReferenceHelper.add_reference(ast_node, node_id, ref_id, ref_kind)
                    # call function a in function b, then b refers to a
                    container = ast_node.get_container_parent()
                    if container.kind == 'FunctionDef':
                        node_id = container.name
                        ref_id = ast_node.node.func.id
                        ref_kind = 'FuncCall'
                        ReferenceHelper.add_reference(ast_node, node_id, ref_id, ref_kind)
        except:
            pass

    @staticmethod
    def add_reference(ast_node: PythonASTNode, node_id: str, ref_id: str, ref_kind: str) -> None:
        properties: dict[str, Any] = {}
        if node_id == ref_id:
            return
        reference = PythonASTReference(ref_id, ref_kind, properties)
        referenced_by = PythonASTReference(node_id, ref_kind, properties)
        try:
            ast_node.translation_unit._references[node_id].append(reference)
        except:
            ast_node.translation_unit._references[node_id] = [reference]
        try:
            ast_node.translation_unit._referenced_by[ref_id].append(referenced_by)
        except:
            ast_node.translation_unit._referenced_by[ref_id] = [referenced_by]


types = ['int', 'float', 'str', 'list', 'set', 'tuple', 'Mapping', 'dict', 'Optional']
if __name__ == "__main__":
    pass

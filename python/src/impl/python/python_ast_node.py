import ast
from functools import cache
from pathlib import Path
import sys
from typing import Any, Optional, Sequence
from common import Stream

from syntax_tree import ASTNode, ASTReference, ASTFinder
from typing_extensions import override

EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []
MATCH_ONE = '_MatchOne__'
MATCH_ALL = '_MatchAll__'


class PythonASTReference():
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
        has_error = False
        errors = ''
        for d in self.atu.type_ignores:
            if d.severity >= 3:
                has_error = True
                errors += f'{d.severity}: {d.spelling} at {d.location}\n'
            print(f'{d.severity}: {d.spelling} at {d.location}')
        if has_error:
            raise Exception(f'Error parsing: {self.file_name} \n+ errors: {errors}')
        # Function to visit all nodes

    def lazy_create_refers(self, node: 'PythonASTNode') -> None:
        if self.references_initialized:
            return
        node.root.process(ReferenceHelper.create_references)
        self.references_initialized = True

    def derive_target_name(self, call, cls, fun, globals: dict[Any, Any]) -> Any:
        if hasattr(call.node.value, 'id'):
            target = call.node.value.id.replace('self', cls.name)
        if hasattr(call.node.value, 'func'):
            target = call.node.value.func.id.replace('self', fun.name)
        for arg in fun.node.args.args:
            if arg.annotation:
                self._references[f"{cls.name}.{fun.name}[{arg.arg}]"] = PythonASTReference(arg.annotation.id, arg.arg,
                                                                                          {})
                target = target.replace(arg.arg, arg.annotation.id)
        for n in globals:
            target = target.replace(n, globals[n])
        return target

    def add_reference(self, call, cls, fun, target):
        src = f"{cls.name}.{fun.name}"
        ref = PythonASTReference(f"{target}::{call.node.attr}", call.node.value.id, {})
        self.append_to_source(src, ref)

    def append_to_source(self, src, ref):
        if src in self._references:
            self._references[src].append(ref)
        else:
            self._references[src] = [ref]

    def convert(self, line_nr, col):
        if (line_nr > len(self.lines)):
            return 0
        return sum(len(self.lines[i]) + 1 for i in range(line_nr - 1)) + col


class ImplicitNode(ast.Name):
    def __init__(self, name, children):
        self.id = name
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
        if(isinstance(node, str)):
            pass
        self.node = node
        self._parent = parent
        self.translation_unit = translation_unit
        cls = type(node)
        self._kind = cls.__name__
        self.indent = ''
        self._name = self._derive_name()

        self.show_props =False
        self._children = []
        self.orelse = []
        self._properties={}
        self._expression=None
        if translation_unit:
            self._filename = translation_unit.file_name
            self.translation_unit = translation_unit
            self.derive_position(node, translation_unit)
            self.add_node()
        else:
            self._filename = ''
            self._length = 0
            self._offset = 0
            self.translation_unit = None

        if (isinstance(node, str)):
            self._kind = 'Name'
            return
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Name) ) or isinstance(node, ast.Name):
                id = node.id if isinstance(node, ast.Name) else node.value.id
                if id.startswith(MATCH_ONE):
                    self._kind = MATCH_ONE
                elif id.startswith(MATCH_ALL):
                    self._kind = MATCH_ALL
        for name in node._fields:
            try:
                child = getattr(node, name)
                match child:
                    case list():  # Matches any list
                        if isinstance(node, ImplicitNode) or isinstance(node, ast.Module) or len(node._fields)==1:
                            for n in child:
                                self._children.append(PythonASTNode(n, translation_unit,self))
                        else:
                            self._children.append(PythonASTNode(ImplicitNode(name,child), translation_unit,self))
                    case ast.AST():
                        if name not in ['ctx', 'ctx']:
                            self._children.append(PythonASTNode(child, translation_unit,self))
                    case _:
                        if name not in ['None']:
                            self.properties[name] = child
            except AttributeError as e:
                print(e)
                continue

    def __eq__(self, other:ASTNode):
        if not other:
            return False
        for i,child in enumerate(self._children):
            if child != other.children[i]:
                return False
        for prop in self.properties:
            if self.properties[prop] != other.properties[prop]:
                return False
        return True
    def derive_position(self, node: ast.AST , translation_unit: PythonTranslationUnit):
        if hasattr(node, 'lineno'):
            self._offset = self.translation_unit.convert(self.node.lineno, self.node.col_offset)
            self._length = self.translation_unit.convert(self.node.end_lineno, self.node.end_col_offset) - self.offset
        elif isinstance(node, ast.Module) and translation_unit:
            self._offset = 0
            self._length = len(translation_unit.content)
        elif isinstance(node, ast.Call):
            self._offset = 0
            self._length = 0
        else:
            self._offset = 0
            self._length = 0
        #
        # if (isinstance(node, str)):
        #     self.name = node
        #     self.__kind = 'Name'
        #     return
        # if (isinstance(node, ast.Assign)):
        #     self.node = node
        # for name in node._fields:
        #     try:
        #         child = getattr(node, name)
        #     except AttributeError:
        #         keywords = True
        #         continue
        #     if child is None and getattr(self.node, name, ...) is None:
        #         keywords = True
        #         continue
        #     match child:
        #         case ast.AST():
        #             if type(child) not in [ast.Load, ast.Store]:
        #                 self._children.append(PythonASTNode(child, translation_unit, self))
        #         case list():  # Matches any list
        #             if isinstance(node, ImplicitNode) or isinstance(node, ast.Module):
        #                 for n in child:
        #                     if not isinstance(n, ast.AST):
        #                         n = ImplicitNode(n, None)
        #                     self._children.append(PythonASTNode(n, translation_unit, self))
        #             elif not name in ['keywords', 'type_ignores'] and child:
        #                 self._children.append(PythonASTNode(ImplicitNode(name, child), translation_unit, self))
        #         case str():
        #             if name == 'id':
        #                 self._name = child
        #         case int():
        #             if name == 'value':
        #                 self._name = str(child)
        #         case _:
        #             pass
        #     self.attributes = {}
        #     try:
        #         value = getattr(node, name)
        #     except AttributeError:
        #         continue
        #     if value is None and getattr(self.node, name, ...) is None:
        #         continue
        #     self.attributes[name] = value

    @override
    @staticmethod
    def load(file_path: Path, extra_args: Sequence[str], working_dir: Path) -> 'PythonASTNode':
        args = [*extra_args, *PythonASTNode.parse_args]
        with open(working_dir / file_path, 'r') as file:
            content = file.read()
            return PythonASTNode.load_from_text(content, file_path, args[3:], working_dir)

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
        elif isinstance(self.node, ast.Call):
            name = ast.unparse(self.node)
        else:
            name = self.kind
        # if isinstance(self.node, ast.Name):
        #     name = self.node.id
        # elif isinstance(self.node, ast.Constant):
        #     name = str(self.node.value)
        # elif isinstance(self.node, ast.Expr) and isinstance(self.node.value, ast.Call):
        #     name = self.node.value.func.id
        # elif isinstance(self.node, ast.Expr) and isinstance(self.node.value, ast.Name):
        #     name = self.node.value.id
        # elif isinstance(self.node, ast.Call):
        #     name = ast.unparse(self.node)
        # else:
        #     name = ''
        return name.replace(MATCH_ALL, '$$').replace(MATCH_ONE, '$')

    @override
    @cache
    def _get_containing_filename(self) -> str:
        return self.translation_unit.file_name if self.translation_unit else ""

    def _is_statement_or_declaration(self):
        return isinstance(self.node, ast.stmt)

    @override
    @property
    def raw_signature(self) -> str:
        return self.binary_file_content().decode(sys.getfilesystemencoding())

    @override
    def binary_file_content(self) -> bytes:
        return self.translation_unit.content[self.offset:self.end_offset] if self.translation_unit else ast.unparse(
            self.node).encode(sys.getfilesystemencoding())

    @override
    def _matches_kind(self, node: ASTNode) -> bool:
        return self.kind == node.kind

    @override
    def _get_parent(self) -> Optional['PythonASTNode']:
        return self.parent

    @override
    def _is_statement(self) -> bool:
        return isinstance(self.node, ast.stmt)

    @override
    @property
    def referenced_by(self) -> Sequence[ASTReference]:
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
            .map(lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    def _addTokens(self, result: dict[str, str], *token_kind):
        for token in self.node.get_tokens():
            # find all attr of token that are of type str or int
            kind = str(token.kind).split('.')[-1]
            if kind in token_kind:
                result[kind] = token.spelling

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

    @staticmethod
    def _is_reference(node):
        try:
            print(type(node))
            print(vars(node))
            print(dir(node))
            print(node.__dict__)
            node.__dict__['id']
            return True
        except:
            return False

    @staticmethod
    @cache
    def __is_property(key, value):
        return callable(value) and any(key.startswith(tag) for tag in ['is_', 'get'])

    @staticmethod
    def _is_wrapped(cursor):
        return cursor.kind.is_unexposed() and len(list(cursor.get_children())) == 1

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

class ReferenceHelper:
    @staticmethod
    def create_references(ast_node: PythonASTNode) -> None:
        assert isinstance(ast_node, PythonASTNode), f'Expected PythonASTNode but got {type(ast_node)}'
        try:
            match ast_node.kind:
                case 'Name':
                    if ref_id not in types:
                        node_id = ast_node.id
                        ref_id = ref_node.id
                        ref_kind = 'TypeRef'
                        ReferenceHelper.add_reference(ast_node, node_id, ref_id, ref_kind)
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
                    #if isinstance(ast_node.node.value, ast.Call):
                     #   node_id = ast_node.node.target.id
                      #  ref_node = ast_node.node.value.func
                       # ref_id = ref_node.id
                       # ref_kind = 'CallRef'
                   # if isinstance(ast_node.node.value, ast.Name):
                    #    node_id = ast_node.node.target.id
                      #  ref_node = ast_node.node.value
                      #  ref_id = ref_node.id
                      #  ref_kind = 'ParamRef'
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
        properties = []
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

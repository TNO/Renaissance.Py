import ast
from functools import cache
from pathlib import Path
import re
import sys
from typing import Any, Optional, Sequence

from textx import get_children

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
        PythonTranslationUnit.cache[file_name] = content
        self.lines = self.content.splitlines()

        self.references: dict[str, list[PythonASTReference]] = {}
        self.referenced_by: dict[str, list[PythonASTReference]] = {}
        self.nodes: dict[str, 'PythonASTNode'] = {}

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

    def lazy_create_references(self, atu) -> None:
        if self.references:
            return
        globals = {}
        for var in ASTFinder.find(atu, 'Assign'):
            for n in var.node.targets:
                if isinstance(n, ast.Name) and isinstance(var.node.value, ast.Call):
                    if isinstance(n, ast.Name) and isinstance(var.node.value.func, ast.Name):
                        globals[n.id] = var.node.value.func.id
                        ref = PythonASTReference(var.node.value.func.id, n.id, {})
                        self.append_to_source(n.id, ref)
        for cls in ASTFinder.find(atu, 'ClassDef'):
            for fun in ASTFinder.find(cls, 'FunctionDef'):
                for call in ASTFinder.find(fun, 'Attribute'):
                    target = self.derrive_target_name(call, cls, fun, globals)
                    self.add_reference(call, cls, fun, target)
        self.references_initialized = True

    def derrive_target_name(self, call, cls, fun, globals: dict[Any, Any]) -> Any:
        target = call.node.value.id.replace('self', cls.name)
        for arg in fun.node.args.args:
            if arg.annotation:
                self.references[f"{cls.name}.{fun.name}[{arg.arg}]"] = PythonASTReference(arg.annotation.id, arg.arg,
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
        if src in self.references:
            self.references[src].append(ref)
        else:
            self.references[src] = [ref]

    def convert(self, line_nr, col):
        if (line_nr > len(self.lines)):
            return 0
        return sum(len(self.lines[i]) + 1 for i in range(line_nr - 1)) + col

    @staticmethod
    def _collect_expansions(translation_unit) -> set[tuple[str, int, int]]:
        result: set[tuple[str, int, int]] = set()
        for child in translation_unit.cursor.get_children():
            if child.kind.name == 'MACRO_INSTANTIATION':
                result.add((child.extent.start.file, child.extent.start.offset, child.extent.end.offset))
        return result


class ImplicitNode(ast.Name):
    def __init__(self, name, children):
        self.id = name
        self.body = children
        self.lineno = 0
        self.col_offset = 0
        self.end_lineno = 0
        self.end_col_offset = 0

    _fields = (
        'body',
    )


class PythonASTNode(ASTNode):
    _attributes = (
        'translation_unit',
        'parent',
        'offset',
        'length',
        'kind',
        'name'
        'offset',
    )
    _fields = ('expresion', 'body', 'alt_body')

    def __init__(self, node: ast.AST, translation_unit: PythonTranslationUnit = None, parent=None,
                 start_offset: Optional[int] = None, length: Optional[int] = None, insert_kind: Optional[str] = None):
        super().__init__(self if parent is None else parent.root)
        if(isinstance(node, str)):
            pass
        self.node = node
        self.parent = parent
        cls = type(node)
        self.kind = cls.__name__
        self.indent = ''
        self.name = self._derive_name()
        self.text = ast.unparse(self.node)
        if translation_unit:
            self.file_name = translation_unit.file_name
            self.translation_unit = translation_unit
        else:
            self.file_name = None
            self.translation_unit = None
        self._children = []
        # convert later
        if (isinstance(node, ast.stmt) or isinstance(node, ast.expr)) and translation_unit and self.node.lineno:
            self.offset = self.translation_unit.convert(self.node.lineno, self.node.col_offset)
            self.length = self.translation_unit.convert(self.node.end_lineno, self.node.end_col_offset) - self.offset
        elif isinstance(node, ast.Module) and translation_unit:
            self.offset = 0
            self.length = len(translation_unit.content)
        else:
            self.offset = 0
            self.length = 0

        if (isinstance(node, str)):
            self.name = node
            self.__kind = 'Name'
            return
        if (isinstance(node, ast.Assign)):
            self.node = node
        for name in node._fields:
            try:
                child = getattr(node, name)
            except AttributeError:
                keywords = True
                continue
            if child is None and getattr(cls, name, ...) is None:
                keywords = True
                continue
            match child:
                case ast.AST():
                    if type(child) not in [ast.Load, ast.Store]:
                        self._children.append(PythonASTNode(child, translation_unit))
                case list():  # Matches any list
                    if isinstance(node, ImplicitNode) or isinstance(node, ast.Module):
                        for n in child:
                            if not isinstance(n, ast.AST):
                                n = ImplicitNode(n, None)
                            self._children.append(PythonASTNode(n, translation_unit))
                    elif not name in ['keywords', 'type_ignores'] and child:
                        self._children.append(PythonASTNode(ImplicitNode(name, child), translation_unit))
                case str():
                    if name == 'id':
                        self.name = child
                case int():
                    if name == 'value':
                        self.name = str(child)
                case _:
                    pass
            self.attributes = {}
            try:
                value = getattr(node, name)
            except AttributeError:
                continue
            if value is None and getattr(cls, name, ...) is None:
                continue
            self.attributes[name] = value
    def __repr__(self):
        raw_lines = self.text.splitlines()
        properties_text = self.get_properties()
        prefix = " " if len(raw_lines) < 2 else "\n{self.indent}"
        formatted_lines = [f"{prefix}|{line}|" for line in raw_lines]
        return f"{self.indent}({self.kind}, {self.name}, {self.file_name}[{self.offset}:{self.length}]){properties_text}: {''.join(formatted_lines)}\n"

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
        # TODO: solve else where bug in matcher
        text = text.replace('()()', '(  )')
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

    @override
    def _get_start_offset(self) -> int:
        return self.offset

    @override
    def _get_length(self) -> int:
        return self.length

    @override
    @cache
    def _get_extended_end_offset(self) -> int:
        return self.offset + self.length

    def _is_statement_or_declaration(self):
        return isinstance(self.node, ast.stmt)

    @override
    def _get_kind(self) -> str:
        return self.kind

    @override
    def get_raw_signature(self) -> str:
        return self.get_binary_file_content().decode(sys.getfilesystemencoding())

    @override
    def get_binary_file_content(self) -> bytes:
        return self.translation_unit.content[self.offset:self.length] if self.translation_unit else ast.unparse(
            self.node).encode(sys.getfilesystemencoding())

    @override
    def _matches_kind(self, node: ASTNode) -> bool:
        return self.kind == node.get_kind()

    @override
    @cache
    def _get_properties(self) -> dict[str, int | str]:
        self.attributes

    @override
    def _get_parent(self) -> Optional['PythonASTNode']:
        return self.parent

    @override
    def _is_statement(self) -> bool:
        return isinstance(self.node, ast.stmt)

    @override
    @cache
    def _get_children(self):
        return self._children

    @override
    @cache
    def _get_name(self):
        return self.name

    @override
    @cache
    def _get_referenced_by(self) -> Sequence[ASTReference]:
        self.translation_unit.lazy_create_references(self)
        node_id = self.node.hash
        ref_by = self.translation_unit._referenced_by.get(node_id, EMPTY_LIST)
        # if both the function declaration and function definition are avaible 
        # the references are stored in the function definition
        # but we want them to also show up in the declaration
        if len(ref_by) == 0:
            definition = self._get_function_definition()
            if definition:
                ref_by = self.translation_unit._referenced_by.get(definition.node.hash, EMPTY_LIST)
        return Stream(ref_by) \
            .map(
            lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    def _get_function_definition(self):
        return None

    @override
    def is_part_of_translation_unit(self) -> bool:
        return self.kind not in ['ImplicitNode']

    @override
    def get_indent(self) -> int:
        # TODO
        return 0

    @override
    @cache
    def _get_references(self) -> Sequence[ASTReference]:
        self.translation_unit.lazy_create_references(self)
        return Stream(self.translation_unit._references.get(self.node.hash, EMPTY_LIST)) \
            .map(
            lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    def _addTokens(self, result: dict[str, str], *token_kind):
        for token in self.node.get_tokens():
            # find all attr of token that are of type str or int
            kind = str(token.kind).split('.')[-1]
            if kind in token_kind:
                result[kind] = token.spelling

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


if __name__ == "__main__":
    pass

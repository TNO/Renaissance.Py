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

from ast import AST

EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []

STMT_PARENTS = [ 'COMPOUND_STMT', 'TRANSLATION_UNIT' ]


PRINT_ALL_NODES = True
class PythonASTReference():
    def __init__(self, node_id:str, ref_kind:str, properties:dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties


class PythonTranslationUnit():
    def __init__(self, atu, file_name:str):
        self.atu = atu
        self.file_name = file_name
        self.references_initialized = False
        print_node_kind(atu)
    # references are used as a cache to store the references of a node
    # the are stored as id for lazy creation
        self._references: dict[str, list[PythonASTReference]] = {}
        self._referenced_by: dict[str, list[PythonASTReference]] = {}
        self._nodes: dict[str, 'PythonASTNode'] = {}

    def lazy_create_references(self, node: 'PythonASTNode') -> None:
        if self.references_initialized:
            return
        node.root.process(ReferenceHelper.create_references)
        self.references_initialized = True

    @staticmethod
    def _collect_expansions(translation_unit) -> set[tuple[str,int,int]]:
        result: set[tuple[str,int,int]] = set()
        for child in translation_unit.cursor.get_children():
            if child.kind.name == 'MACRO_INSTANTIATION':
                result.add((child.extent.start.file, child.extent.start.offset, child.extent.end.offset))
        return result

class ImpliciteNode(ast.Name):
    def __init__(self,name, children):
        self.id =name
        self.body=children


    _fields = (
        'body',
    )
    _field_types = {
        'body': list[ast.stmt],
    }
    __annotations__ = {
        'body': list[ast.stmt],
     }
    __match_args__ = (
        'body',
    )

class PythonASTNode(ASTNode):
    def __init__(self, node:ast.AST, translation_unit:PythonTranslationUnit=None,  parent =  None, start_offset: Optional[int] = None, length: Optional[int] = None, insert_kind : Optional[str]=None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self.parent = parent
        if translation_unit:
            self.file_name = translation_unit.file_name
            self.translation_unit = translation_unit
        else:
            self.file_name = None
            self.translation_unit = None
        self._children = []
        #convert later
        if(isinstance(node, ast.stmt)):
            self._start_offset = node.lineno*100000+node.col_offset
            self._length = node.end_lineno*100000+node.end_col_offset
        else:
            self._start_offset = 0
            self._length = 0

        cls = type(node)
        self.__kind = cls.__name__
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
                    if type(child)!= ast.Load:
                        self._children.append(PythonASTNode(child))
                case list():  # Matches any list
                    if isinstance(node, ImpliciteNode):
                        for n in child:
                            self._children.append(PythonASTNode(n))
                    elif not name in ['keywords', 'type_ignores'] and child:
                        self._children.append(PythonASTNode(ImpliciteNode(name, child)))
                case str():
                    if name=='id':
                        self.__name = child
                case int():
                    if name=='value':
                        self.__name = str(child)
                case _:
                    pass
            self.attributes={}
            try:
                value = getattr(node, name)
            except AttributeError:
                continue
            if value is None and getattr(cls, name, ...) is None:
                continue
            self.attributes[name]=value

        # match type(node):
        #     case ast.Expr:
        #         if isinstance(node.value, ast.Call):
        #             for arg in node.value.args:
        #                 self._children.append(PythonASTNode(arg))
        #
        #     case ast.If:
        #         self._children.append(PythonASTNode(node.test))
        #         body = PythonASTNode(ImpliciteNode() )
        #         for stmt in node.body:
        #             body._children.append(PythonASTNode(stmt))
        #         self._children.append(body)
        #         orelse = PythonASTNode(ImpliciteNode())
        #         for stmt in node.orelse:
        #             orelse._children.append(PythonASTNode(stmt))
        #         self._children.append(orelse)
        #     case ast.For:
        #         body = PythonASTNode(ImpliciteNode())
        #         for stmt in node.body:
        #             body._children.append(PythonASTNode(stmt))
        #         self._children.append(body)
        #     case ast.Module:
        #         for stmt in node.body:
        #             self._children.append(PythonASTNode(stmt))
        #     case _:
        #         pass

    @override
    @staticmethod
    def load(file_path: Path, extra_args:Sequence[str], working_dir:Path) -> 'PythonASTNode':
        args=[*extra_args, *PythonASTNode.parse_args]
        translation_unit = PythonASTNode.index.parse(working_dir / file_path, args=args[3:])
        PythonASTNode.check_diagnostics(translation_unit, file_path.name)
        root_node =  PythonASTNode(translation_unit, PythonTranslationUnit(translation_unit, file_name=str(file_path)), None)
        return root_node

    @override
    @staticmethod
    def load_from_text(text: str, file_name: str, extra_args:Sequence[str], working_dir:Path) -> "PythonASTNode":
        translation_unit = ast.parse(text, file_name)
        PythonASTNode.check_diagnostics(translation_unit, file_name)
        root_node =  PythonASTNode(translation_unit, PythonTranslationUnit(translation_unit, file_name=str(file_name)), None)
        # Convert file_content to bytes
        file_content_bytes = text.encode(sys.getfilesystemencoding())
        # add to cache to avoid reading the file again
        root_node.cache[file_name] = file_content_bytes
        PythonASTNode.check_diagnostics(translation_unit, file_name)
        return root_node

    @staticmethod
    def check_diagnostics(translation_unit, file_name: str) -> None:
        has_error = False
        errors = ''
        for d in translation_unit.type_ignores:
            if d.severity >= 3:
                has_error = True
                errors += f'{d.severity}: {d.spelling} at {d.location}\n'    
            print(f'{d.severity}: {d.spelling} at {d.location}')
        if has_error:
            raise Exception(f'Error parsing: {file_name} \n+ errors: {errors}')
    
    @override
    def _get_name(self) -> str:
        if isinstance(self.node, ast.Name):
            return self.node.id
        elif isinstance(self.node, ast.Constant):
            return self.node.value
        elif isinstance(self.node, ast.Expr) and isinstance(self.node.value, ast.Call):
            return self.node.value.func.id
        elif isinstance(self.node, ast.Expr) and isinstance(self.node.value, ast.Name):
            return self.node.value.id
        elif isinstance(self.node, ast.Call):
            return self.node.func.id
        else:
            return ''

    @override
    @cache
    def _get_containing_filename(self) -> str:
        return self.file_name

    @override
    def _get_start_offset(self) -> int: 
        return self._start_offset

    @override
    def _get_length(self) -> int: 
        return self._length

    @override
    @cache
    def _get_extended_end_offset(self) -> int: 
        try: 
            endOffset =  self.__start_offset + self.__length
            if (not self._is_statement_or_declaration()) and (self.parent and self.parent.get_kind() in STMT_PARENTS):  
                content = self.root.get_binary_file_content()
                while endOffset < len(content) and not content[endOffset-1] in b';':
                    endOffset += 1
            return endOffset
        except:
            return 0

    def _is_statement_or_declaration(self):
        return re.match('.*(_STMT|_DECL|CXX_METHOD)', self.get_kind())

    @override
    def _get_kind(self) -> str: 
        return self.node.__class__.__name__

    @override
    def get_raw_signature(self) -> str:
        return ast.unparse(self.node)
    @override
    def _matches_kind(self, node:ASTNode) -> bool: 
        return self.__kind == node.get_kind() or\
            (self.__kind.endswith('_LITERAL') and node.get_kind()=='DECL_REF_EXPR') or\
            (self.__kind=='DECL_REF_EXPR' and node.get_kind().endswith('_LITERAL'))\

    @override
    @cache
    def _get_properties(self) -> dict[str, int|str]: 
        result  =  {}
        offsets = (self.get_containing_filename(), self.get_start_offset(), self.get_end_offset())
        if self.get_kind() == 'BINARY_OPERATOR':
            #TODO remove below code after clang release that supports the getOpCode() statement
            children = self.get_children()
            start_offset = children[0].get_start_offset() + children[0].get_length()
            end_offset = children[1].get_start_offset()
            operator = self.get_content(start_offset, end_offset)
            result['operator'] = operator.strip()
            # next statement works in C++ but not in Python (yet) will be released later
            # result['operator'] =  self.node.getOpCode()
        elif self.get_kind() == 'UNARY_OPERATOR':
            #TODO remove below code after clang release that supports the getOpCode() statement
            child = self.get_children()[0]
            #list all attributes of self.node excluding the once starting with _

            if child.get_start_offset() > self.get_start_offset():
                start_offset = self.get_start_offset()
                end_offset = child.get_start_offset()
                prefix_operator = True
            else:
                start_offset = child.get_start_offset() + child.get_length()
                end_offset = self.get_start_offset() + self.get_length()
                prefix_operator = False

            operator = self.get_content(start_offset, end_offset)
            result['operator'] = operator.strip()
            result['prefixOperator'] = prefix_operator
            # next statement works in C++ but not in Python (yet) will be released later
            # result['operator'] =  self.node.getOpCode()
        elif self.get_kind().endswith('_LITERAL'):
            self._addTokens(result, 'LITERAL')
        elif self.get_kind() =='DECL_REF_EXPR':
            self._addTokens(result, 'LITERAL')

        is_all = { attr[len('is_'):]: True for attr in dir(self.node) if attr.startswith('is_') and  callable(getattr(self.node, attr) and getattr(self.node, attr)() == True)}
        result.update(is_all)
        return result
    
    @override
    def _get_parent(self) -> Optional['PythonASTNode']:
        return  self.parent

    @override
    def _is_statement(self) ->bool:
        return isinstance(self.node, ast.stmt)
    
    @override
    @cache
    def _get_children(self):
        return self._children
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
        return Stream(ref_by)\
            .map(lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    def _get_function_definition(self):
        if self.node.type.kind == TypeKind.FUNCTIONPROTO: # type: ignore
            signature = self.node.displayname
            semantic_parent = self.node.semantic_parent.hash
            def has_body(node):
               return  any(c.kind == CursorKind.COMPOUND_STMT for c in node.node.get_children())  # type: ignore
            def is_match(node):
                if node.__kind != self.__kind: return False
                if node.node.type.kind != TypeKind.FUNCTIONPROTO: return False # type: ignore
                if node.node.semantic_parent.hash != semantic_parent: return False
                if node.node.displayname != signature: return False
                return has_body(node)           
            
            if has_body(self):
                return None
            body = ASTFinder.find_all(self.root, is_match).find_first().or_else(None) # type: ignore
            if isinstance(body, PythonASTNode):
                return body
        return None
    @override
    def is_part_of_translation_unit(self) -> bool:
        return True
    @override
    def get_indent(self) -> int:
        return 0
    @override
    @cache
    def _get_references(self) -> Sequence[ASTReference]:
        self.translation_unit.lazy_create_references(self)
        return Stream(self.translation_unit._references.get(self.node.hash, EMPTY_LIST))\
            .map(lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()


    def _addTokens(self,  result: dict[str,str], *token_kind):
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
        return callable(value) and any( key.startswith( tag) for tag in ['is_', 'get'] )

    @staticmethod
    def _is_wrapped(cursor):
        return cursor.kind.is_unexposed() and len(list(cursor.get_children())) == 1

class ReferenceHelper():
    @staticmethod
    def create_references(ast_node: PythonASTNode) -> None:
        assert isinstance(ast_node, PythonASTNode), f'Expected PythonASTNode but got {type(ast_node)}'
        references = []
        node_id: str = ast_node.node.hash
        ast_node.translation_unit._references[node_id] = references
        ref_fields = ['referenced'] #, 'type.get_declaration()']
        for field in ref_fields:
            try:
                element = eval('ast_node.node.' + field)
                if element.kind.name == 'NO_DECL_FOUND':    
                    continue
                ref_id = element.hash
                ref_kind = field.split(".")[0]
                properties = {k:p for k, p in element.__dict__.items() if not k.startswith('_') and k != 'hash'}
                if node_id == ref_id:
                    return
                reference = PythonASTReference(ref_id, ref_kind, properties)
                referenced_by = PythonASTReference(node_id, ref_kind, {k:p for k, p in ast_node.node.__dict__.items() if k != 'hash'})
                try:
                    ast_node.translation_unit._referenced_by[ref_id].append(referenced_by)
                except:
                    ast_node.translation_unit._referenced_by[ref_id] = [referenced_by]
                references.append(reference)
            except:
                pass


if __name__ == "__main__":
    pass
    # Set the path to libclang.so
    # clang.cindex.Config.set_library_file('C:/Users/pnelissen/scoop/apps/llvm/current/bin/libclang.dll')
    # root = PythonASTNode.load(Path('Z:/testproject/c/src/main.c'))

    # root.translation_unit.save('Z:/testproject/c/src/main.c.ast')

    # def visitFunction(astNode: ASTNode) -> None:
    #     parent = astNode.get_parent()
    #     depth = 0
    #     while parent:
    #         depth += 1
    #         parent = parent.get_parent()
    #     print(str('  ' * depth) + astNode.get_kind())

    # # root.process(visitFunction)

    # ASTShower.show_node(root)

class PythonImpliciteBlock(PythonASTNode):
    def __init__(self, parent, kind, children):
        self.root = parent.root
        self.node = None
        self.parent = parent
        self.file_name = None
        self.translation_unit = None
        self._start_offset = 0
        self._length = 0
        self._children=[]
        self.__kind = "__ADDED__"
        for child in children:
            self._children.append(PythonASTNode(child))

    @override
    def get_raw_signature(self) -> str:
        return ''

            # Function to visit all nodes
def print_node_kind(node: ast.AST, depth=0):
    if PRINT_ALL_NODES:
        print(f"{' '*depth} Node: {ast.dump(node)}, Kind: {node.__class__.__name__}")
        if 'body' in dir(node):
            for child in node.body:
                print_node_kind(child, depth+2)


def save_get(target, key):
    try:
        return getattr(target,key)()
    except:
        return None
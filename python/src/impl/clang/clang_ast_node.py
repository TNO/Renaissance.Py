from functools import cache
from pathlib import Path
import re
import sys
from typing import Any, Optional, Sequence
from common import Stream

from syntax_tree import ASTNode, ASTReference, ASTFinder, TextUtils
from typing_extensions import override

from clang.cindex import TranslationUnit, Index, Config, CursorKind, TypeKind

from syntax_tree.ast_node import MATCH_ONE, MATCH_ALL

EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []

STMT_PARENTS = [ 'COMPOUND_STMT', 'TRANSLATION_UNIT' ]


PRINT_ALL_NODES = False
class ClangASTReference():
    def __init__(self, node_id:str, ref_kind:str, properties:dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties


class ClangTranslationUnit():
    cache=[]
    def __init__(self, clang_atu:TranslationUnit, file_name:str):
        self.clang_atu = clang_atu
        self.file_name = file_name
        self.references_initialized = False
        print_node_kind(clang_atu.cursor)
        self.macro_expansions = ClangTranslationUnit._collect_expansions(clang_atu)
    # references are used as a cache to store the references of a node
    # the are stored as id for lazy creation
        self._references: dict[str, list[ClangASTReference]] = {}
        self._referenced_by: dict[str, list[ClangASTReference]] = {}
        self._nodes: dict[str, 'ClangASTNode'] = {}

    def lazy_create_references(self, node: 'ClangASTNode') -> None:
        if self.references_initialized:
            return
        node.root.process(ReferenceHelper.create_references)
        self.references_initialized = True

    @staticmethod
    def _collect_expansions(translation_unit: TranslationUnit) -> set[tuple[str,int,int]]:
        result: set[tuple[str,int,int]] = set()
        for child in translation_unit.cursor.get_children():
            if child.kind.name == 'MACRO_INSTANTIATION':
                result.add((child.extent.start.file, child.extent.start.offset, child.extent.end.offset))
        return result


class ClangASTNode(ASTNode):
    @staticmethod
    def set_library_path() -> None:
        try: 
            print(Path(__file__).parent.parent.parent.parent / '.venv/Lib/site-packages/clang/native')
            Config.set_library_path(Path(__file__).parent.parent.parent.parent / '.venv/Lib/site-packages/clang/native')
        except Exception as e:  
            print(e)
            
    set_library_path()
    index = Index.create()
    parse_args=['-fparse-all-comments', '-ferror-limit=0', '-Xclang', '-detailed-preprocessing-record', '-fsyntax-only']

    def __init__(self, node, translation_unit:ClangTranslationUnit,  parent =  None, start_offset: Optional[int] = None, length: Optional[int] = None, insert_kind : Optional[str]=None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._children = None
        self._parent = parent
        self.translation_unit = translation_unit
        self.inserted = insert_kind != None
        self.show_props = False
        self._filename = self._get_containing_filename()
        self._name = self._derive_name()
        # if the node has not been added to the translation unit, add it
        # a node might already be added if it is split into multiple nodes
        # an example is for base types like int, char, etc. which are split into multiple nodes
        if self.node.hash not in self.translation_unit._nodes:
            self.translation_unit._nodes[node.hash] = self
        self._offset = start_offset if start_offset != None else self.__derive_start_offset()
        self._length = length if length != None else self.__derive_length()
        self._kind = insert_kind if insert_kind != None else self.__derive_kind()
        self.indent = ''
        # TODO: TextUtils.get_indent(self.content, self._offset)

        # an fake child is introduced to handle the case where the type of a declaration is not found
        # for example in the case of a base type. 
        # without the fake child pattern matching on types will be difficult
        self.__inserted_children = []
        if insert_kind == None and  not self.node.location.is_in_system_header and self.node.kind.is_declaration() and self.node.type.kind != TypeKind.INVALID:  # type: ignore
            loc_offset: int = self.node.location.offset
            length = len(self.node.spelling.encode(sys.getdefaultencoding()))
            insert_child = ClangASTNode(self.node, self.translation_unit, self, loc_offset, length, 'DECL_LOC') 
            insert_child._children = []
            self.__inserted_children.append(insert_child) 
            if self.node.type.get_declaration().kind is CursorKind.NO_DECL_FOUND: # type: ignore
                type = self.node.type if self.node.result_type.kind == TypeKind.INVALID else self.node.result_type # type: ignore
                length_ref = len(type.spelling.encode(sys.getdefaultencoding()))
                insert_child = ClangASTNode(self.node, self.translation_unit, self, self._offset, length_ref, CursorKind.TYPE_REF.name)  # type: ignore
                insert_child._children = []
                self.__inserted_children.append(insert_child)

        self._children = []
        for n in self.__inserted_children:
            self._children.append(n )
        for n in self.node.get_children():
            if not (n.kind.name == 'MACRO_DEFINITION' and n.displayname.startswith('__')):
                self._children.append(ClangASTNode(ClangASTNode.remove_wrapper(n), self.translation_unit, self) )

        self._properties = self._derive_properties()
        self._properties['name'] = self._name



    @override
    @staticmethod
    def load(file_path: Path, extra_args:Sequence[str], working_dir:Path) -> 'ClangASTNode':
        args=[*extra_args, *ClangASTNode.parse_args]
        translation_unit: TranslationUnit = ClangASTNode.index.parse(working_dir / file_path, args=args[3:])
        ClangASTNode.check_diagnostics(translation_unit, file_path.name)
        root_node =  ClangASTNode(translation_unit.cursor, ClangTranslationUnit(translation_unit, file_name=str(file_path)), None)
        return root_node

    @override
    @staticmethod
    def load_from_text(text: str, file_name: str, extra_args:Sequence[str], working_dir:Path) -> "ClangASTNode":
        # Convert file_content to bytes
        file_content_bytes = text.encode(sys.getfilesystemencoding())
        # add to cache to avoid reading the file again
        ASTNode.cache[file_name] = file_content_bytes
        translation_unit: TranslationUnit = ClangASTNode.index.parse(file_name, unsaved_files=[(file_name, text)],  args=[*ClangASTNode.parse_args,*extra_args])
        ClangASTNode.check_diagnostics(translation_unit, file_name)
        root_node =  ClangASTNode(translation_unit.cursor, ClangTranslationUnit(translation_unit, file_name=str(file_name)), None)
        ClangASTNode.check_diagnostics(translation_unit, file_name)
        return root_node

    @staticmethod
    def check_diagnostics(translation_unit: TranslationUnit, file_name: str) -> None:
        has_error = False
        errors = ''
        for d in translation_unit.diagnostics:
            if d.severity >= 3:
                has_error = True
                errors += f'{d.severity}: {d.spelling} at {d.location}\n'    
            print(f'{d.severity}: {d.spelling} at {d.location}')
        if has_error:
            raise Exception(f'Error parsing: {file_name} \n+ errors: {errors}')
    
    @override
    def _derive_name(self) -> str:
        try:
            if self.node.type.kind == TypeKind.RECORD: # type: ignore
                return self.node.type.spelling
        except:
            pass
        try:
            return self.node.spelling
        except: 
            pass
        return EMPTY_STR

    @override
    @cache
    def _get_containing_filename(self) -> str:
        if self is self.root:
            return self.translation_unit.clang_atu.spelling
        try: 
            return self.node.location.file.name 
        except:
            return EMPTY_STR


    @override
    @property
    def extended_end_offset(self) -> int:
        try: 
            endOffset = self._offset + self._length
            if (not self._is_statement_or_declaration()) and (self.parent and self.parent.kind in STMT_PARENTS):
                content = self.root.binary_file_content()
                while endOffset < len(content) and not content[endOffset-1] in b';':
                    endOffset += 1
            return endOffset
        except:
            return 0

    def _is_statement_or_declaration(self):
        return re.match('.*(_STMT|_DECL|CXX_METHOD)', self.kind)

    @override
    def matches_kind(self, node:ASTNode) -> bool:
        return self._kind == node.kind or\
            (self._kind.endswith('_LITERAL') and node.kind == 'DECL_REF_EXPR') or\
            (self._kind =='DECL_REF_EXPR' and node.kind.endswith('_LITERAL'))\

    @override
    @cache
    def _derive_properties(self) -> dict[str, int|str]:
        result  =  {}
        offsets = (self.filename, self.offset, self.end_offset)
        if offsets in self.translation_unit.macro_expansions:
            result['macro_expansion'] = self.text

        if self.kind == 'BINARY_OPERATOR':
            #TODO remove below code after clang release that supports the getOpCode() statement
            children = self.children
            start_offset = children[0].offset + children[0].length
            end_offset = children[1].offset
            operator = self.content(start_offset, end_offset)
            result['operator'] = operator.strip()
            # next statement works in C++ but not in Python (yet) will be released later
            # result['operator'] =  self.node.getOpCode()
        elif self.kind == 'UNARY_OPERATOR':
            #TODO remove below code after clang release that supports the getOpCode() statement
            child = self.children[0]
            #list all attributes of self.node excluding the once starting with _

            if child.offset > self.offset:
                start_offset = self.offset
                end_offset = child.offset
                prefix_operator = True
            else:
                start_offset = child.offset + child.length
                end_offset = self.offset + self.length
                prefix_operator = False

            operator = self.content(start_offset, end_offset)
            result['operator'] = operator.strip()
            result['prefixOperator'] = prefix_operator
            # next statement works in C++ but not in Python (yet) will be released later
            # result['operator'] =  self.node.getOpCode()
        elif self.kind.endswith('_LITERAL'):
            self._addTokens(result, 'LITERAL')
        elif self.kind == 'DECL_REF_EXPR':
            self._addTokens(result, 'LITERAL')

        is_all = { attr[len('is_'):]: True for attr in dir(self.node) if attr.startswith('is_') and  callable(getattr(self.node, attr) and getattr(self.node, attr)() == True)}
        result.update(is_all)
        return result
    
    @override
    @property
    def is_statement(self) ->bool:
        return self.parent is not None and self.parent.kind in STMT_PARENTS
    
    @override
    @property
    def referenced_by(self) -> [ASTReference]:
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
                if node._kind != self._kind: return False
                if node.node.type.kind != TypeKind.FUNCTIONPROTO: return False # type: ignore
                if node.node.semantic_parent.hash != semantic_parent: return False
                if node.node.displayname != signature: return False
                return has_body(node)           
            
            if has_body(self):
                return None
            body = ASTFinder.find_all(self.root, is_match).find_first().or_else(None) # type: ignore
            if isinstance(body, ClangASTNode):
                return body
        return None

    @override
    @property
    def references(self) -> [ASTReference]:
        self.translation_unit.lazy_create_references(self)
        return Stream(self.translation_unit._references.get(self.node.hash, EMPTY_LIST))\
            .map(lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()


    def _addTokens(self,  result: dict[str,str], *token_kind):
            for token in self.node.get_tokens():
                # find all attr of token that are of type str or int
                kind = str(token.kind).split('.')[-1]
                if kind in token_kind:
                    result[kind] = token.spelling

    def __derive_start_offset(self) -> int: 
        try: 
            return self.node.extent.start.offset
        except:
            return 0

    def __derive_length(self) -> int: 
        try: 
            endOffset =  self.node.extent.end.offset
            return endOffset - self.__derive_start_offset()
        except:
            return 0

    def __derive_kind(self) -> str:
        try:
            if self.node.kind.name == 'MACRO_DEFINITION':
                return str(self.node.kind.name)
            elif self.node.kind.name in ['UNEXPOSED_EXPR','VAR_DECL','DECL_REF_EXPR']:
                if self.node.displayname.startswith('$$') and ' ' not in self.node.displayname:
                    return MATCH_ALL
                elif self.node.displayname.startswith('$') and ' ' not in self.node.displayname:
                    return MATCH_ONE
            return str(self.node.kind.name)
        except Exception as e:
            return EMPTY_STR

    @staticmethod
    def remove_wrapper(cursor):
        try:
            if ClangASTNode._is_wrapped(cursor):
                return  ClangASTNode.remove_wrapper(list(cursor.children)[0])
        except:
            pass
        return cursor

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
        return cursor.kind.is_unexposed() and len(list(cursor.children)) == 1

class ReferenceHelper():
    @staticmethod
    def create_references(ast_node: ClangASTNode) -> None:
        assert isinstance(ast_node, ClangASTNode), f'Expected ClangASTNode but got {type(ast_node)}'
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
                reference = ClangASTReference(ref_id, ref_kind, properties)
                referenced_by = ClangASTReference(node_id, ref_kind, {k:p for k, p in ast_node.node.__dict__.items() if k != 'hash'})
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
    # root = ClangASTNode.load(Path('Z:/testproject/c/src/main.c'))

    # root.translation_unit.save('Z:/testproject/c/src/main.c.ast')

    # def visitFunction(astNode: ASTNode) -> None:
    #     parent = astNode.get_parent()
    #     depth = 0
    #     while parent:
    #         depth += 1
    #         parent = parent.get_parent()
    #     print(str('  ' * depth) + astNode.kind)

    # # root.process(visitFunction)

    # ASTShower.show_node(root)


# Function to visit all nodes
def print_node_kind(node, depth=0):
    if PRINT_ALL_NODES:
        print(f"{' '*depth} Node: {node.spelling}, Kind: {node.kind}")
        
        for child in node.children:
            print_node_kind(child, depth+2)


def save_get(target, key):
    try:
        return getattr(target,key)()
    except:
        return None
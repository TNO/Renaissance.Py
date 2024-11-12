# create a class that inherits syntax tree ASTNode

from functools import cache
import json
import os
from pathlib import Path
import tempfile
from common import Stream
from syntax_tree import ASTNode
from typing import Any, Optional, TypeVar
from typing_extensions import override
import subprocess


EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []

STMT_PARENTS = [ 'CompoundStmt', 'TranslationUnitDecl' ]

VERBOSE = False

class ClangJsonTranslationUnit():
    def __init__(self, json_root, file_name:str):
        self.json_root = json_root
        # references are used as a cache to store the references of a node
        # the are stored as id for lazy creation
        self._references: dict[str, list[str]] = {}
        self._referenced_by: dict[str, list[str]] = {}
        self._nodes: dict[str, ClangJsonASTNode] = {}
        self.file_name = file_name
        
    
class ClangJsonASTNode(ASTNode):
    parse_args=['-fparse-all-comments', '-ferror-limit=0', '-Xclang', '-ast-dump=json', '-fsyntax-only']

    def __init__(self, node: dict[str, Any], translation_unit: ClangJsonTranslationUnit, parent: Optional['ClangJsonASTNode'] = None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._children: Optional[list['ClangJsonASTNode']] = None
        self.parent = parent
        self.translation_unit = translation_unit
        self.translation_unit._nodes[node['id']] = self

    @override
    @staticmethod
    def load(file_path:Path, extra_args:list[str] = []) -> 'ClangJsonASTNode':
        #in a shell process compile the file_path with clang compiler
        try:
            clang = 'clang++' if file_path.suffix == '.cpp' else 'clang'
            command = [clang, *ClangJsonASTNode.parse_args, *extra_args, file_path]
            result = subprocess.run(command, capture_output=True, text=True)
            temp_dir = tempfile.gettempdir()
            temp_file_name = os.path.join(temp_dir, file_path.name+'.ast.json')
            with open(temp_file_name, 'w') as temp_file:
                if VERBOSE: print ('result stored in ' + temp_file_name)
                temp_file.write(result.stdout)

            json_atu = json.loads(result.stdout)
            atu = ClangJsonASTNode(json_atu, translation_unit=ClangJsonTranslationUnit(json_atu, file_name=str(file_path)) )
            # cache the result of the temp file before deleting it
            atu.get_content(0, 0)

            atu.process(ClangJsonASTNode.__create_references)
            return atu

        except Exception as e:
            print('Call to clang failed. Did you install clang?, is it on the env path?')
            raise e
        
    @override
    @staticmethod
    def load_from_text(file_content: str, file_name: str='test.c', extra_args:list[str] = []) -> 'ClangJsonASTNode':
        # Define the directory for the temporary file
        temp_dir = tempfile.gettempdir()
        # Define the name of the temporary file
        temp_file_name = os.path.join(temp_dir,file_name)
        # Write text to the temporary file
        with open(temp_file_name, 'wb') as temp_file:
            temp_file.write(file_content.encode('utf-8'))        # write the text to a temporary file
        result = ClangJsonASTNode.load(Path(temp_file_name), extra_args)
        # Delete the temporary file
        os.remove(temp_file_name)
        return result

    @override
    def _get_containing_filename(self) -> str:
        if self.node.get('isImplicit', False):
            return ''
        if self.node.get('implicit', False):
            return ''
        if not self.parent:
            return self.translation_unit.file_name
        # return the file name of the node if it exists else return the file name of the parent node
        containing_file =  self._get(['loc', 'file'], EMPTY_STR)
        if containing_file:
            return containing_file
        included_file =  self._get(['loc', 'includedFrom', 'file'], '')
        if included_file: #included but no file location is provided in the node so we don't know the file name
            return ''
        included_file =  self._get(['loc', 'spellingLoc', 'includedFrom', 'file'], '')
        if included_file: #included but no file location is provided in the node so we don't know the file name
            return ''
        # not included and no file location so it is the same as the parent
        if self.parent:
            return self.parent.get_containing_filename()
        return EMPTY_STR
    
    @override
    def _get_start_offset(self) -> int: 
        offset = self._get(['range', 'begin', 'offset'], default=-1)
        if offset == -1:
            #we might be dealing with a macro in that case use the expansion location
            offset = self._get(['range', 'begin', 'expansionLoc', 'offset'], default=0)
        return offset


    @override
    def _get_length(self) -> int: 
        if(self.get_kind() == 'TranslationUnitDecl'):
            return len(self.get_binary_file_content(self.get_containing_filename()))
        offset = self._get(['range', 'end', 'offset'], default=-1)
        tokLen = self._get(['range', 'end', 'tokLen'], default=-1)
        if offset == -1:
            #we might be dealing with a macro in that case use the expansion location
            offset = self._get(['range', 'end', 'expansionLoc', 'offset'], default=0)
            tokLen = self._get(['range', 'end', 'expansionLoc', 'tokLen'], default=0)

        return offset + tokLen - self.get_start_offset()

    @override
    def _get_kind(self) -> str: 
        return self.node.get('kind', EMPTY_STR)

    @override
    def _get_properties(self) -> dict[str, int|str]: 
        # get all the attributes of self.node except the inner  nodes, id, location, range, kind and name and all reference nodes (that is children with 'id)
        properties = {k: v for k, v in self.node.items() if ClangJsonASTNode.__is_property(k) and not ClangJsonASTNode._is_reference(v)}
        return properties

   
    @override
    def _get_referenced_by(self) -> list['ClangJsonASTNode']:
        return Stream(self.translation_unit._referenced_by.get(self.node['id'], EMPTY_LIST))\
            .map(lambda ref_id: self.translation_unit._nodes[ref_id]).to_list()

    @override
    def _get_references(self) -> list['ClangJsonASTNode']:
        return Stream(self.translation_unit._references.get(self.node['id'], EMPTY_LIST))\
            .map(lambda ref_id: self.translation_unit._nodes[ref_id]).to_list()

    @override
    def _get_parent(self) -> Optional['ClangJsonASTNode']: 
        return self.parent

    @override
    def _is_statement(self) -> bool:
        return self.parent != None and self.parent.get_kind() in STMT_PARENTS
    
    @override
    def _get_children(self) -> list['ClangJsonASTNode']: 
        if self._children is None:
            self._children = [ ClangJsonASTNode(ClangJsonASTNode._remove_wrapper(n), translation_unit=self.translation_unit, parent=self) for n in self.node.get('inner', []) if not n.get('isImplicit', False)]
        return self._children
    
    @override
    def _get_name(self) -> str:
        name = self.node.get('name')
        if name:
            return name
        if self.get_kind() =='DeclRefExpr':
            return self._get(['referencedDecl', 'name'], default=EMPTY_STR)
        return self.node.get('name', EMPTY_STR)

    @staticmethod
    def _remove_wrapper(node):
        try:
            if ClangJsonASTNode._is_wrapped(node):
                return  ClangJsonASTNode._remove_wrapper(list(node['inner'])[0])
        except:
            pass
        return node

    @staticmethod
    def _is_reference(json_node):
        return isinstance(json_node, dict) and json_node.get('id')

    @staticmethod
    @cache
    def __is_property(key):
        return key not in ['id', 'inner', 'loc', 'range', 'kind', 'name', 'isUsed', 'isReferenced', 'referencedDecl', 'previousDecl', 'mangledName']

    @staticmethod
    def _is_wrapped(node):
        return node['kind'].startswith("Implicit") and len(list(node['inner'])) == 1

    T = TypeVar('T')
    def _get(self, path: list[str], default: T) -> T:
        assert default is not None, 'default value must be provided'
        target = self.node
        try:
            for p in path:
                target = target[p]
            return target if isinstance(target,type(default)) else default
        except:
            return default

    @staticmethod
    def __create_references(ast_node) -> None:
        assert isinstance(ast_node, ClangJsonASTNode), f'Expected ClangJsonASTNode but got {type(ast_node)}'
        references = []
        node_id = ast_node.node['id']
        ast_node.translation_unit._references[node_id] = references
        refs = [v for k, v in ast_node.node.items() if not ClangJsonASTNode.__is_property(k) and ClangJsonASTNode._is_reference(v)]
        for ref in refs:
            ref_id = ref['id']
            try:
                ast_node.translation_unit._referenced_by[ref_id].append(node_id)
            except:
                ast_node.translation_unit._referenced_by[ref_id] = [node_id]
            references.append(ref_id)

# create a class that inherits syntax tree ASTNode

from dataclasses import dataclass
from functools import cache
import json
import os
from pathlib import Path
import re
import tempfile
from common import Stream
from syntax_tree import ASTNode, ASTReference
from typing import Any, Optional, Sequence, TypeVar
from typing_extensions import override
import subprocess


EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []
ID_TAGS = ['id', 'typeAliasDeclId', 'templateDeclId', 'templateSpecializationDeclId', 'referencedDeclId']

STMT_PARENTS = [ 'CompoundStmt', 'TranslationUnitDecl' ]

VERBOSE = False

class ClangJsonASTReference():
    def __init__(self, node_id:str, ref_kind:str, properties:dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties

class ClangJsonTranslationUnit():
    def __init__(self, json_root:dict[str, Any], file_name:str):
        self.json_root = json_root
        self.file_name = file_name
        self.references_initialized = False
        # references are used as a cache to store the references of a node
        # the are stored as id for lazy creation
        self._references: dict[str, list[ClangJsonASTReference]] = {}
        self._referenced_by: dict[str, list[ClangJsonASTReference]] = {}
        self._nodes: dict[str, 'ClangJsonASTNode'] = {}
    
    def lazy_create_references(self, root: 'ClangJsonASTNode') -> None:
        if self.references_initialized:
            return
        root.process(ReferenceHelper.create_references)
        root.process(ReferenceHelper.add_record_references)
        self.references_initialized = True

class ClangJsonASTNode(ASTNode):
    parse_args=['-fparse-all-comments', '-ferror-limit=0', '-Xclang', '-ast-dump=json', '-fsyntax-only']

    def __init__(self, node: dict[str, Any], translation_unit: ClangJsonTranslationUnit, parent: Optional['ClangJsonASTNode'] = None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._children: Optional[Sequence['ClangJsonASTNode']] = None
        self.parent = parent
        self.translation_unit = translation_unit
        self.translation_unit._nodes[node['id']] = self

    @override
    @staticmethod
    def load(file_path:Path, extra_args:Sequence[str] = []) -> 'ClangJsonASTNode':
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
            return atu

        except Exception as e:
            print('Call to clang failed. Did you install clang?, is it on the env path?')
            raise e
        
    @override
    @staticmethod
    def load_from_text(file_content: str, file_name: str='test.c', extra_args:Sequence[str] = []) -> 'ClangJsonASTNode':
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
    @cache
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
    @cache
    def _get_length(self) -> int: 
        return self._get_end_offset() - self.get_start_offset()

    @cache
    def _get_end_offset(self) -> int: 
        if(self.get_kind() == 'TranslationUnitDecl'):
            return len(self.get_binary_file_content(self.get_containing_filename()))
        offset = self._get(['range', 'end', 'offset'], default=-1)
        tokLen = self._get(['range', 'end', 'tokLen'], default=-1)
        if offset == -1:
            #we might be dealing with a macro in that case use the expansion location
            offset = self._get(['range', 'end', 'expansionLoc', 'offset'], default=0)
            tokLen = self._get(['range', 'end', 'expansionLoc', 'tokLen'], default=0)

        return offset + tokLen

    @override
    @cache
    def _get_extended_end_offset(self) -> int: 
        try: 
            endOffset =  self._get_end_offset()
            if (not self._is_statement_or_declaration()) and (self.parent and self.parent.get_kind() in STMT_PARENTS):  
                content = self.root.get_binary_file_content()
                while endOffset < len(content) and not content[endOffset-1] in b';':
                    endOffset += 1
            return endOffset
        except:
            return 0

    def _is_statement_or_declaration(self):
        return re.match('(?i).*(Stmt|Decl)', self.get_kind())

    @override
    @cache
    def _get_kind(self) -> str: 
        return self.node.get('kind', EMPTY_STR)

    @override
    @cache
    def _get_properties(self) -> dict[str, Any]: 
        # get all the attributes of self.node except the inner  nodes, id, location, range, kind and name and all reference nodes (that is children with 'id)
        properties = {k: ClangJsonASTNode._remove_ids(v) for k, v in self.node.items() if ClangJsonASTNode.__is_property(k) and not ClangJsonASTNode._is_reference(v)==None}
        if self._get(['range', 'end', 'expansionLoc', 'offset'], -1) != -1: #dealing with a macro expansion
            properties['macro_expansion'] = self.get_text()
        return properties
   
    @override
    @cache
    def _get_referenced_by(self) -> Sequence[ASTReference['ClangJsonASTNode']]:
        self.translation_unit.lazy_create_references(self)
        return Stream(self.translation_unit._referenced_by.get(self.node['id'], EMPTY_LIST))\
            .map(lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    @override
    @cache
    def _get_references(self)-> Sequence[ASTReference['ClangJsonASTNode']]:
        self.translation_unit.lazy_create_references(self)
        return Stream(self.translation_unit._references.get(self.node['id'], EMPTY_LIST))\
            .map(lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    @override
    def _get_parent(self) -> Optional['ClangJsonASTNode']: 
        return self.parent

    @override
    def _is_statement(self) -> bool:
        return self.parent != None and self.parent.get_kind() in STMT_PARENTS
    
    @override
    @cache
    def _get_children(self) -> Sequence['ClangJsonASTNode']: 
        if self._children is None:
            self._children = [ ClangJsonASTNode(ClangJsonASTNode._remove_wrapper(n), translation_unit=self.translation_unit, parent=self) for n in self.node.get('inner', []) if not n.get('isImplicit', False)]
        return self._children
    
    @override
    @cache
    def _get_name(self) -> str:
        name = self.node.get('name')
        if name:
            return name
        if self.get_kind() =='DeclRefExpr':
            return self._get(['referencedDecl', 'name'], default=EMPTY_STR)
        if self.get_kind() =='StringLiteral':
            return self._get(['value'], default=EMPTY_STR)
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
    def _remove_ids(json_node):
        if not isinstance(json_node, dict):
            return json_node
        return {k:v for k, v in json_node.items() if not k in ID_TAGS}  

    @staticmethod
    def _is_reference(json_node):
        return len(ReferenceHelper._get_reference_ids(json_node)) > 0

    @staticmethod
    @cache
    def __is_property(key):
        return key not in ['id', 'inner', 'loc', 'range', 'kind', 'name', 'isUsed', 'isReferenced', 'referencedDecl', 'previousDecl', 'mangledName']

    @staticmethod
    def _is_wrapped(node):
        return node['kind'].startswith("Implicit") and len(list(node['inner'])) == 1

    T = TypeVar('T')
    def _get(self, path: Sequence[str], default: T) -> T:
        assert default is not None, 'default value must be provided'
        target = self.node
        try:
            for p in path:
                target = target[p]
            return target if isinstance(target,type(default)) else default
        except:
            return default

class ReferenceHelper:

    @staticmethod
    def create_references(ast_node) -> None:
        assert isinstance(ast_node, ClangJsonASTNode), f'Expected ClangJsonASTNode but got {type(ast_node)}'
        references = []
        node_id = ast_node.node['id']
        ast_node.translation_unit._references[node_id] = references
        refs = {k:v for k, v in ast_node.node.items() if not ReferenceHelper._is_child_node(k) and ClangJsonASTNode._is_reference(v)}
        for kind, ref in refs.items():
            for ref_id in ReferenceHelper._get_reference_ids(ref):
                properties = {k:p for k, p in ref.items() if k != ref_id}
                reference = ClangJsonASTReference(ref_id, kind, properties)
                referenced_by = ClangJsonASTReference(node_id, kind, properties)
                try:
                    ast_node.translation_unit._referenced_by[ref_id].append(referenced_by)
                except:
                    ast_node.translation_unit._referenced_by[ref_id] = [referenced_by]
                references.append(reference)

    @staticmethod
    def add_record_references(ast_node) -> None:
        """
        Json does not contain direct references between classes and their base classes.

        Hence these references are created in this method.

        This method checks if the given AST node is of kind 'CXXRecordDecl' and has a tag 'class'.
        If so, it processes the base classes of the node and creates references for them.

        Args:
            ast_node (ClangJsonASTNode): The AST node to process.

        Raises:
            AssertionError: If the provided ast_node is not an instance of ClangJsonASTNode.
        """
        assert isinstance(ast_node, ClangJsonASTNode), f'Expected ClangJsonASTNode but got {type(ast_node)}'
        bases = ast_node._get(['bases'], [])
        if not bases:
            bases = [ast_node.node] if ast_node.node.get('type') else None
        if not bases:
            return
        node_id = ast_node.node['id']
        for base in bases:
            ref_id = ReferenceHelper._get_record_decl(ast_node, base)
            if ref_id:
                properties = {k:p for k, p in base.items() if k != 'type'}
                reference = ClangJsonASTReference(ref_id, 'base', properties)
                referenced_by = ClangJsonASTReference(node_id, 'base', properties)
                try:
                    ast_node.translation_unit._referenced_by[ref_id].append(referenced_by)
                except:
                    ast_node.translation_unit._referenced_by[ref_id] = [referenced_by]
                try:
                    ast_node.translation_unit._references[node_id].append(reference)
                except:
                    ast_node.translation_unit._references[node_id] = [reference]

    @staticmethod
    def _get_record_decl(ast_node, base):
        try:
            tp = base['type']
            # split desugaredQualType to derive the parent namespaces
            namespaces = tp['desugaredQualType'].split('::')[:-1][::-1]
            qual_type = tp['qualType']
            for id, node in ast_node.translation_unit._nodes.items():
                if node.get_kind() == 'CXXRecordDecl' and node.get_name() == qual_type:
                    parent = node.get_parent()
                    for ns in namespaces:
                        if ns != parent.get_name() or parent.get_kind() != 'NamespaceDecl':
                            return None
                        parent = parent.get_parent()
                    return id
        except:
            return None

    @staticmethod
    def _get_reference_ids(json_node):
        result = []
        if not isinstance(json_node, dict):
            return result
        for key in ID_TAGS:
           value = json_node.get(key)
           if value != None:
               result.append(value)
        return result

    @staticmethod
    @cache
    def _is_child_node(key):
        return key in ['inner']



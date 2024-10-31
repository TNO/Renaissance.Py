# create a class that inherits syntax tree ASTNode

from functools import cache
import json
import os
from pathlib import Path
import tempfile
from syntax_tree.ast_node import ASTNode
from typing import Any, Optional, TypeVar
from typing_extensions import override
import subprocess


EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []

STMT_PARENTS = [ 'CompoundStmt', 'TranslationUnitDecl' ]

class ClangJsonASTNode(ASTNode):
    parse_args=['-fparse-all-comments', '-ferror-limit=0', '-Xclang', '-ast-dump=json', '-fsyntax-only']

    def __init__(self, node: dict[str, Any], translation_unit, parent: Optional['ClangJsonASTNode'] = None, file_name=''):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._children: Optional[list['ClangJsonASTNode']] = None
        self.parent = parent
        self.translation_unit = translation_unit
        self.file_name = file_name

    @staticmethod
    def load(file_path:Path) -> 'ClangJsonASTNode':
        #in a shell process compile the file_path with clang compiler
        try:
            command = ['clang', *ClangJsonASTNode.parse_args, file_path]
            result = subprocess.run(command, capture_output=True, text=True)
            temp_dir = tempfile.gettempdir()
            temp_file_name = os.path.join(temp_dir, file_path.name+'.ast.json')
            with open(temp_file_name, 'w') as temp_file:
                print ('result stored in ' + temp_file_name)
                temp_file.write(result.stdout)

            json_atu = json.loads(result.stdout)
            return ClangJsonASTNode(json_atu, translation_unit=json_atu, file_name=str(file_path))
        except Exception as e:
            print('Call to clang failed. Did you install clang?, is it on the env path?')
            raise e
        
    @override
    @staticmethod
    def load_from_text(file_content: str, file_name: str='test.c') -> 'ClangJsonASTNode':
        # Define the directory for the temporary file
        temp_dir = tempfile.gettempdir()
        # Define the name of the temporary file
        temp_file_name = os.path.join(temp_dir,file_name)
        # Write text to the temporary file
        with open(temp_file_name, 'w') as temp_file:
            temp_file.write(file_content)        # write the text to a temporary file
        result = ClangJsonASTNode.load(Path(temp_file_name))
        # cache the result of the temp file before deleting it
        result.get_content(0, len(file_content))
        # Delete the temporary file
        os.remove(temp_file_name)
        return result

    @override
    def get_containing_filename(self) -> str:
        if self.file_name:
            return self.file_name
        # return the file name of the node if it exists else return the file name of the parent node
        containing_file =  self._get(['loc', 'file'], None)
        if containing_file is None and not self.parent is None:
            return self.parent.get_containing_filename()
        return EMPTY_STR
    
    @override
    def get_start_offset(self) -> int: 
        return self._get(['range', 'begin', 'offset'], default=0)

    @override
    def get_length(self) -> int: 
        if(self.get_kind() == 'TranslationUnitDecl'):
            return len(self._get_binary_file_content(self.get_containing_filename()))
        return self._get(['range', 'end', 'offset'], default=0) + self._get(['range', 'end', 'tokLen'], default=0) - self.get_start_offset()

    @override
    def get_kind(self) -> str: 
        return self.node.get('kind', EMPTY_STR)

    @override
    def get_properties(self) -> dict[str, int|str]: 
        result  =  {}
        if self.get_kind() == 'BinaryOperator':
            result['operator'] = self.node['opcode']
        elif self.get_kind() == 'UnaryOperator':
            result['operator'] = self.node['opcode']
            result['prefixOperator'] = not self.node['isPostfix']
        elif self.get_kind().endswith('Literal'):
            result['value'] = self.node['value']
        elif self.get_kind() =='DeclRefExpr':
            pass
        return result
    
    @override
    def get_parent(self) -> Optional['ClangJsonASTNode']: 
        return self.parent

    def is_statement(self) -> bool:
        return self.parent != None and self.parent.get_kind() in STMT_PARENTS
    
    @override
    def get_children(self) -> list['ClangJsonASTNode']: 
        if self._children is None:
            self._children = [ ClangJsonASTNode(ClangJsonASTNode._remove_wrapper(n), translation_unit=self.translation_unit, parent=self) for n in self.node.get('inner', []) if not n.get('isImplicit', False)]
        return self._children
    
    @override
    def get_name(self) -> str:
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
    def _is_wrapped(node):
        return node['kind'].startswith("Implicit") and len(list(node['inner'])) == 1

    T = TypeVar('T')
    def _get(self, path: list[str], default: T) -> T:
        target = self.node
        try:
            for p in path:
                target = target[p]
            return target if isinstance(target,type(default)) else default
        except:
            return default


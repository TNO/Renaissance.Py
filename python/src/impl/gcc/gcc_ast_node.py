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
from textx import metamodel_from_file, metamodel_from_str



EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []

STMT_PARENTS = [ 'CompoundStmt', 'TranslationUnitDecl' ]

# Load the grammar from the gimplegcc.tx file
gimple_mm = metamodel_from_file(Path(__file__).parent / 'gimple_gcc.tx')

class GccAstNode(ASTNode):
    parse_args=['-fpermissive', '-fdump-tree-gimple-raw-lineno']

    def __init__(self, node: dict[str, Any], translation_unit, parent: Optional['GccAstNode'] = None, file_name=''):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._children: Optional[list['GccAstNode']] = None
        self.parent = parent
        self.translation_unit = translation_unit
        self.file_name = file_name

    @staticmethod
    def load(file_path:Path) -> 'GccAstNode':
        #in a shell process compile the file_path with clang compiler
        try:
            # if file_path extension is c used gcc else use g++
            temp_dir = tempfile.gettempdir()
            temp_gimple_file_name = ''
            temp_o_file_name = os.path.join(temp_dir, file_path.name+'.o')
            executable =  'gcc' if file_path.suffix in ['.c', '.h'] else 'g++'
            #delete previous files
            for f in os.listdir(temp_dir):
                if file_path.name in f:
                    os.remove(os.path.join(temp_dir, f))

            command = [executable, *GccAstNode.parse_args + ['-o', temp_o_file_name] , file_path]
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                print(result.stdout)
                print(result.stderr)
                raise Exception('Call to gcc failed. Did you install gcc?, is it on the env path?')
            #get the gimple file
            for f in os.listdir(temp_dir):
                if file_path.name in f and f.endswith('.gimple'):
                    temp_gimple_file_name = os.path.join(temp_dir, f)

            print ('result stored in ' + temp_gimple_file_name)
            #read temp gimple file as a string
            with open(temp_gimple_file_name, 'r') as temp_file:
                gimple_file_content = temp_file.read()
                escaped_gimple_file_content = gimple_file_content.replace('->', '$$')
                gimple_model_atu = gimple_mm.model_from_str(escaped_gimple_file_content)
                return GccAstNode(gimple_model_atu, translation_unit=gimple_model_atu, file_name=str(file_path))
        except Exception as e:
            print(e)
            print('Call to gcc failed. Did you install gcc?, is it on the env path?')
            raise e
        
    @override
    @staticmethod
    def load_from_text(file_content: str, file_name: str='test.c') -> 'GccAstNode':
        # Define the directory for the temporary file
        temp_dir = tempfile.gettempdir()
        # Define the name of the temporary file
        temp_file_name = os.path.join(temp_dir,file_name)
        # Write text to the temporary file
        with open(temp_file_name, 'w') as temp_file:
            temp_file.write(file_content)        # write the text to a temporary file
        result = GccAstNode.load(Path(temp_file_name))
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
    def get_parent(self) -> Optional['GccAstNode']: 
        return self.parent

    def is_statement(self) -> bool:
        return self.parent != None and self.parent.get_kind() in STMT_PARENTS
    
    @override
    def get_children(self) -> list['GccAstNode']: 
        if self._children is None:
            self._children = [ GccAstNode(GccAstNode._remove_wrapper(n), translation_unit=self.translation_unit, parent=self) for n in self.node.get('inner', []) if not n.get('isImplicit', False)]
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
            if GccAstNode._is_wrapped(node):
                return  GccAstNode._remove_wrapper(list(node['inner'])[0])
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

if __name__ == '__main__':
    # file = Path(__file__).parent.parent.parent.parent.parent / 'c/src/test.cpp'
    # GccAstNode.load(file)
    gimple_test_mm = metamodel_from_str("""
Model:
    elements*=Function
;

Function:
    names+=ID '(' ')' gimple_bind=GimpleBind
;

GimpleBind:
    'gimple_bind' '<' '>'
;
                                        


                                     
""")

    gimple_mm.model_from_str(r'test () gimple_bind <>')
    gimple_mm.model_from_str(r'intd test () gimple_bind <>')
    gimple_mm.model_from_str(r'intd test () [Z:\testproject\c\src\test.cpp:53:1] gimple_bind <>')
    gimple_mm.model_from_str(r'gimple_assign <eq_expr, retval.0, _1, 0, NULL>')
    gimple_mm.model_from_str(r'A::~A (struct A * const this) gimple_bind <>')
    gimple_mm.model_from_str(r'[Z:\testproject\c\src\test.cpp:18:10] gimple_assign <ssa_name, this$$_vptr.A, _1, NULL, NULL>')

    gimple_mm.model_from_str(r'[Z:\testproject\c\src\test.cpp:49:14] gimple_assign <eq_expr, retval.0, _1, 0, NULL>')

    with open(r'C:\Users\PNELIS~1\AppData\Local\Temp\1\test.cpp.o-test.cpp.006t.gimple', 'r') as temp_file:
        gimple_file_content = temp_file.read()
        escaped_gimple_file_content = gimple_file_content.replace('->', '$$')
        gimple_model_atu = gimple_mm.model_from_str(escaped_gimple_file_content)





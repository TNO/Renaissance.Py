from functools import cache
from pathlib import Path
from typing import Optional
from syntax_tree.ast_node import ASTNode
from typing_extensions import override
import re

from clang.cindex import TranslationUnit, Index, Config, CursorKind

EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []

STMT_PARENTS = [ 'COMPOUND_STMT', 'TRANSLATION_UNIT' ]

class ClangASTNode(ASTNode):
    print(Path(__file__).parent.parent.parent.parent / '.venv/Lib/site-packages/clang/native')
    Config.set_library_path(Path(__file__).parent.parent.parent.parent / '.venv/Lib/site-packages/clang/native')
    index = Index.create()
    parse_args=['-fparse-all-comments', '-ferror-limit=0', '-Xclang', '-ast-dump=json', '-fsyntax-only']

    def __init__(self, node, translation_unit:TranslationUnit,  parent =  None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self.skipped_node = None
        self._children = None
        self.parent = parent
        self.translation_unit = translation_unit

    @override
    @staticmethod
    def load(file_path: Path) -> 'ClangASTNode':
        translation_unit: TranslationUnit = ClangASTNode.index.parse(file_path, args=ClangASTNode.parse_args)
        return ClangASTNode(translation_unit.cursor, translation_unit, None)

    @override
    @staticmethod
    def load_from_text(file_content: str, file_name: str='test.c') -> 'ClangASTNode':
        translation_unit: TranslationUnit = ClangASTNode.index.parse(file_name, unsaved_files=[(file_name, file_content)],  args=ClangASTNode.parse_args)
        rootNode =  ClangASTNode(translation_unit.cursor, translation_unit, None)
        # Convert file_content to bytes
        file_content_bytes = file_content.encode('utf-8')
        # add to cache to avoid reading the file again
        rootNode.cache[file_name] = file_content_bytes
        return rootNode
    
    @override
    def get_name(self) -> str:
        try:
            return self.node.spelling #TODO fix
        except: 
            return EMPTY_STR

    @override
    def get_containing_filename(self) -> str:
        if self is self.root:
            return self.translation_unit.spelling
        try: 
            return self.node.location.file.name 
        except:
            return EMPTY_STR
    
    @override
    def get_start_offset(self) -> int: 
        try: 
            return self.node.extent.start.offset
        except:
            return 0

    @override
    @cache
    def get_length(self) -> int: 
        try: 
            endOffset =  self.node.extent.end.offset
            return endOffset - self.get_start_offset()
        except:
            return 0

    @override
    def get_kind(self) -> str: 
        try:
            return str(self.node.kind.name)
        except Exception as e:
            return EMPTY_STR

    @override
    def get_properties(self) -> dict[str, int|str]: 
        result  =  {}
            
        if self.get_kind() == 'BINARY_OPERATOR':
            #TODO remove below code after clang release that supports the getOpCode() statement
            children = self.get_children()
            start_offset = children[0].get_start_offset() + children[0].get_length()
            end_offset = children[1].get_start_offset()
            operator = self.get_content(start_offset, end_offset)
            result['operator'] = operator.strip()
            # next statement works in C++ but not in Python (yet) will be released later
            # result['operator'] =  self.node.getOpCode()
        if self.get_kind().endswith('_LITERAL'):
            self.addTokens(result, 'LITERAL')
        if self.get_kind() =='DECL_REF_EXPR':
            self.addTokens(result, 'LITERAL')

        is_all = { attr[len('is_'):]: getattr(self.node, attr)() for attr in dir(self.node) if attr.startswith('is_') and  getattr(self.node, attr)()}
        result.update(is_all)
        return result
    
    @override
    def get_parent(self) -> Optional['ClangASTNode']: 
        return  self.parent

    def is_statement(self) ->bool:
        return self.parent != None and self.parent.get_kind() in STMT_PARENTS
    
    @override
    def get_children(self) -> list['ClangASTNode']: 
        if self._children is None:
            self._children = [ ClangASTNode(ClangASTNode.remove_wrapper(n), self.translation_unit, self) for n in self.node.get_children()]
        return self._children

    def addTokens(self,  result: dict[str,str], *tokenKind):
            for token in self.node.get_tokens():
                # find all attr of token that are of type str or int
                kind = str(token.kind).split('.')[-1]
                if kind in tokenKind:
                    result[kind] = token.spelling
    
    @staticmethod
    def remove_wrapper(cursor):
        try:
            if ClangASTNode._is_wrapped(cursor):
                return  ClangASTNode.remove_wrapper(list(cursor.get_children())[0])
        except:
            pass
        return cursor

    @staticmethod
    def _is_wrapped(cursor):
        return cursor.kind.is_unexposed() and len(list(cursor.get_children())) == 1

# Function to recursively visit AST nodes
def visit_node(node, depth=0):
    print('  ' * depth + f'{node.kind} {node.spelling}')
    for child in node.get_children():
        visit_node(child, depth + 1)

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
    #     print(str('  ' * depth) + astNode.get_kind())

    # # root.process(visitFunction)

    # ASTShower.show_node(root)

from functools import cache
from pathlib import Path
from typing import Any, Optional, Sequence
from common import Stream
from syntax_tree import ASTNode, ASTReference
from typing_extensions import override

from clang.cindex import TranslationUnit, Index, Config

EMPTY_DICT = {}
EMPTY_STR = ''
EMPTY_LIST = []

STMT_PARENTS = [ 'COMPOUND_STMT', 'TRANSLATION_UNIT' ]

class ClangASTReference():
    def __init__(self, node_id:str, ref_kind:str, properties:dict[str, Any]) -> None:
        self.node_id = node_id
        self.ref_kind = ref_kind
        self.properties = properties


class ClangTranslationUnit():
    def __init__(self, clang_atu:TranslationUnit, file_name:str):
        self.clang_atu = clang_atu
        self.file_name = file_name
        self.references_initialized = False
    # references are used as a cache to store the references of a node
    # the are stored as id for lazy creation
        self._references: dict[str, list[ClangASTReference]] = {}
        self._referenced_by: dict[str, list[ClangASTReference]] = {}
        self._nodes: dict[str, 'ClangASTNode'] = {}

    def lazy_create_references(self, root: 'ClangASTNode') -> None:
        if self.references_initialized:
            return
        root.process(ReferenceHelper.create_references)
        self.references_initialized = True


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
    parse_args=['-fparse-all-comments', '-ferror-limit=0', '-Xclang', '-ast-dump=json', '-fsyntax-only']

    def __init__(self, node, translation_unit:ClangTranslationUnit,  parent =  None):
        super().__init__(self if parent is None else parent.root)
        self.node = node
        self._children = None
        self.parent = parent
        self.translation_unit = translation_unit
        self.translation_unit._nodes[node.hash] = self


    @override
    @staticmethod
    def load(file_path: Path,  extra_args=[]) -> 'ClangASTNode':
        translation_unit: TranslationUnit = ClangASTNode.index.parse(file_path, args=[*ClangASTNode.parse_args,*extra_args])
        root_node =  ClangASTNode(translation_unit.cursor, ClangTranslationUnit(translation_unit, file_name=str(file_path)), None)
        return root_node

    @override
    @staticmethod
    def load_from_text(file_content: str, file_name: str='test.c', extra_args=[]) -> 'ClangASTNode':
        translation_unit: TranslationUnit = ClangASTNode.index.parse(file_name, unsaved_files=[(file_name, file_content)],  args=[*ClangASTNode.parse_args,*extra_args])
        root_node =  ClangASTNode(translation_unit.cursor, ClangTranslationUnit(translation_unit, file_name=str(file_name)), None)
        # Convert file_content to bytes
        file_content_bytes = file_content.encode('utf-8')
        # add to cache to avoid reading the file again
        root_node.cache[file_name] = file_content_bytes
        return root_node
    
    @override
    @cache
    def _get_name(self) -> str:
        try:
            if self.get_kind() not in ['CALL_EXPR']:
                return self.node.spelling #TODO fix
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
    @cache
    def _get_start_offset(self) -> int: 
        try: 
            return self.node.extent.start.offset
        except:
            return 0

    @override
    @cache
    def _get_length(self) -> int: 
        try: 
            endOffset =  self.node.extent.end.offset
            return endOffset - self.get_start_offset()
        except:
            return 0

    @override
    @cache
    def _get_kind(self) -> str: 
        try:
            return str(self.node.kind.name)
        except Exception as e:
            return EMPTY_STR

    @override
    @cache
    def _get_properties(self) -> dict[str, int|str]: 
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
            self.addTokens(result, 'LITERAL')
        elif self.get_kind() =='DECL_REF_EXPR':
            self.addTokens(result, 'LITERAL')

        is_all = { attr[len('is_'):]: True for attr in dir(self.node) if attr.startswith('is_') and  callable(getattr(self.node, attr) and getattr(self.node, attr)() == True)}
        result.update(is_all)
        return result
    
    @override
    def _get_parent(self) -> Optional['ClangASTNode']: 
        return  self.parent

    @override
    def _is_statement(self) ->bool:
        return self.parent != None and self.parent.get_kind() in STMT_PARENTS
    
    @override
    @cache
    def _get_children(self) -> Sequence['ClangASTNode']: 
        if self._children is None:
            self._children = [ ClangASTNode(ClangASTNode.remove_wrapper(n), self.translation_unit, self) for n in self.node.get_children()]
        return self._children

    @override
    @cache
    def _get_referenced_by(self) -> Sequence[ASTReference['ClangASTNode']]:
        self.translation_unit.lazy_create_references(self)
        return Stream(self.translation_unit._referenced_by.get(self.node.hash, EMPTY_LIST))\
            .map(lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()

    @override
    @cache
    def _get_references(self) -> Sequence[ASTReference['ClangASTNode']]:
        self.translation_unit.lazy_create_references(self)
        return Stream(self.translation_unit._references.get(self.node.hash, EMPTY_LIST))\
            .map(lambda ref: ASTReference(self.translation_unit._nodes[ref.node_id], ref.ref_kind, ref.properties)).to_list()


    def addTokens(self,  result: dict[str,str], *token_kind):
            for token in self.node.get_tokens():
                # find all attr of token that are of type str or int
                kind = str(token.kind).split('.')[-1]
                if kind in token_kind:
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
    def create_references(ast_node) -> None:
        assert isinstance(ast_node, ClangASTNode), f'Expected ClangASTNode but got {type(ast_node)}'
        references = []
        node_id = ast_node.node.hash
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
    #     print(str('  ' * depth) + astNode.get_kind())

    # # root.process(visitFunction)

    # ASTShower.show_node(root)

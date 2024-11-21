
from pathlib import Path
from typing import Any, Callable, Generic, Iterator, Sequence, TypeVar

from common.stream import Stream
from .ast_finder import ASTFinder
from .match_finder import MatchFinder, PatternMatch
from .ast_rewriter import ASTRewriter
from .ast_factory import ASTFactory
from .ast_node import ASTNode, ASTNodeType

T = TypeVar('T')

class ASTProcessor(Generic[ASTNodeType]):
    def __init__(self, root: ASTNodeType, ast_factory: ASTFactory,  user_objects : dict[str,Any], in_memory=False,) -> None:
        self.__root_node = root
        self.__rewriter = ASTRewriter(root)
        self.__ast_factory = ast_factory
        self.in_memory = in_memory
        self.__user_objects = user_objects
    
    def get_filename(self) -> str:
        return self.__rewriter.get_filename()
    
    def get_root(self) -> ASTNodeType:
        return self.__root_node
    
    def replace(self, new_content:str, target: ASTNode|Sequence[ASTNode]|PatternMatch, include_whitespace: bool = True, include_comments: bool = True):
        self.__rewriter.replace(new_content, target, include_whitespace, include_comments)

    def remove(self, target: ASTNode|Sequence[ASTNode]|PatternMatch, include_whitespace: bool = True, include_comments: bool = True):
        self.__rewriter.remove(target, include_whitespace, include_comments)

    def insert_before(self,new_content:str, target: ASTNode|Sequence[ASTNode]|PatternMatch, include_whitespace: bool = True, include_comments: bool = True):
        self.__rewriter.insert_before(new_content, target, include_whitespace, include_comments)

    def insert_after(self,new_content:str, target: ASTNode|Sequence[ASTNode]|PatternMatch, include_whitespace: bool = True, include_comments: bool = True):
        self.__rewriter.insert_after(new_content, target, include_whitespace, include_comments)
    
    def find_all(self, function: Callable[[ASTNodeType], Iterator[ASTNodeType]]) -> Stream[ASTNodeType]:
        return ASTFinder.find_all(self.__root_node, function)

    def find_kind(self, kind: str) -> Stream[ASTNodeType]:
        return ASTFinder.find_kind(self.__root_node, kind)

    def find_match(self,  *patterns_list: Sequence[ASTNode], recursive=True, exclude_kind=MatchFinder.DEFAULT_EXCLUDE_KIND)-> Stream[PatternMatch]:
        return MatchFinder.find_all(self.__root_node, *patterns_list, recursive=recursive, exclude_kind=exclude_kind)

    def user_object(self, key: str, factory: type[T]) -> T:
        result = self.__user_objects.get(key)
        if not result:
            result = factory()
            self.__user_objects[key] = result
        assert isinstance(result, factory), f"Expected {factory} but got {type(result)}"
        return result
    
    def has_changed(self) -> bool:
        return self.__rewriter.has_changed()

    def apply_to_string(self) -> str:
        return self.__rewriter.apply_to_string()

    def commit(self) -> 'ASTProcessor':
        """
        Commits the current changes to the AST (Abstract Syntax Tree) and returns a new ASTProcessor instance.

        This method applies the current changes to the source code and creates a new ASTProcessor instance
        with the updated AST. If the changes are in-memory, it directly creates the new AST from the updated
        code string. Otherwise, it writes the changes to the file, reloads the file, and then creates the new AST.

        Returns:
            ASTProcessor: A new instance of ASTProcessor with the updated AST.

        Raises:
            IOError: If there is an error writing to the file.
        """
        new_code = self.apply_to_string()
        if (self.__rewriter.has_changed() == False):
            return self
        
        if self.in_memory:
            atu = self.__ast_factory.create_from_text(new_code, str(Path(self.get_filename()).name))
        else:
            #save file first then reload it
            with open(self.get_filename(), 'wb') as f:
                f.write(self.__rewriter.apply())
            # TODO check errors
            atu = self.__ast_factory.create(Path(self.get_filename()))
        return ASTProcessor(atu, self.__ast_factory, self.__user_objects, self.in_memory)

#main
if __name__ == '__main__':
    T = TypeVar('T')
    def test(key: str, factory: type[T]) -> T:
        result = factory()
        assert isinstance(result, factory)
        return result
    
    test('key', str)
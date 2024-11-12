from abc import ABC, abstractmethod
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Callable, Optional, TypeVar




# enum with ABORT, CONTINUE and SKIP
class VisitorResult(Enum):
    ABORT = 0
    CONTINUE = 1
    SKIP = 2

ASTNodeType = TypeVar("ASTNodeType", bound='ASTNode')

# To make usage of the concrete class methods easier, ASTNode must NOT have abstract public classes!!
class ASTNode(ABC):
    """
       The base class to represent an AST node. 
       It is an abstract class that should be inherited by concrete classes that represent specific AST nodes.
    """
    def __init__(self, root: 'ASTNode') -> None:
        super().__init__()
        self.root = root
        self.cache = {}
    
    @cache
    def is_part_of_translation_unit(self) -> bool:
        return self.get_containing_filename() == self.root.get_containing_filename()

    @cache
    def get_raw_signature(self) -> str:
        start = self.get_start_offset()
        end = start + self.get_length()
        if start == end:
            return ""
        file = self.get_containing_filename()
        if not file: 
            return ""
        return self.get_content(start, end)

    def get_content(self, start, end):
        bytes = self.root.get_binary_file_content()
        return str(bytes[start:end], 'utf-8')

    def get_binary_file_content(self, file_path: str|None=None) -> bytes:
        assert self is self.root,  "_getBinaryFileContent can only be used for the root node"
        if not file_path:
            file_path = self.get_containing_filename()
        try:
            return self.cache[file_path]
        except Exception as e:
            with open(file_path, 'rb') as f:
                bytes =  f.read()
                self.cache[file_path] = bytes
                return bytes

    @cache        
    def get_end_offset(self):
        return self.get_start_offset() + self.get_length()
    
    def get_preceding_sibling(self):
        parent = self.get_parent()
        if not parent:
            return None
        siblings = parent.get_children()
        index = siblings.index(self)
        return siblings[index - 1] if index > 0 else None

    def get_next_sibling(self):
        parent = self.get_parent()
        if not parent:
            return None
        siblings = parent.get_children()
        index = siblings.index(self)
        return siblings[index + 1] if index < len(siblings) - 1 else None


    @staticmethod
    @abstractmethod
    def load(file_path: Path, extra_args:list[str])-> 'ASTNode':
        pass

    @staticmethod
    @abstractmethod
    def load_from_text(text: str, file_name: str, extra_args:list[str]) -> 'ASTNode':
        pass

    @cache
    def get_name(self) -> str:
        return self._get_name()

    @cache
    def get_containing_filename(self) -> str:
        return self._get_containing_filename()
    
    @cache
    def get_start_offset(self) -> int: 
        return self._get_start_offset()
    
    @cache
    def get_length(self) -> int: 
        return self._get_length()

    @cache
    def get_kind(self) -> str: 
        return self._get_kind()

    @cache
    def get_properties(self) -> dict[str, int|str]: 
        return self._get_properties()

    @cache
    def get_parent(self: ASTNodeType) -> Optional[ASTNodeType]: 
        return self._get_parent()

    @cache
    def is_statement(self) ->bool: 
        return self._is_statement()

    @cache
    def get_children(self: ASTNodeType) -> list[ASTNodeType]: 
        return self._get_children()

    @cache
    def get_references(self: ASTNodeType) -> list[ASTNodeType]:
        return self._get_references()

    @cache
    def get_referenced_by(self: ASTNodeType) -> list[ASTNodeType]:
        return self._get_referenced_by()

    @abstractmethod
    def _get_name(self) -> str:
        pass

    @abstractmethod
    def _get_containing_filename(self) -> str:
        pass
    
    @abstractmethod
    def _get_start_offset(self) -> int: 
        pass

    @abstractmethod
    def _get_length(self) -> int: 
        pass

    @abstractmethod
    def _get_kind(self) -> str: 
        pass

    @abstractmethod
    def _get_properties(self) -> dict[str, int|str]: 
        pass

    @abstractmethod
    def _get_parent(self: ASTNodeType) -> Optional[ASTNodeType]: 
        pass

    @abstractmethod
    def _is_statement(self) ->bool: 
        pass

    @abstractmethod
    def _get_children(self: ASTNodeType) -> list[ASTNodeType]: 
        pass

    @abstractmethod
    def _get_references(self: ASTNodeType) -> list[ASTNodeType]:
        pass

    @abstractmethod
    def _get_referenced_by(self: ASTNodeType) -> list[ASTNodeType]:
        pass
    
    def process(self, function: Callable[['ASTNode'], None]):
        function(self)
        for child in self.get_children():
            child.process(function)

    def accept(self,  function: Callable[['ASTNode'], VisitorResult]):
        """
        Accepts a visitor function and applies it to the current node and its children.

        Args:
            function (Callable[['ASTNode'], None]): A function that takes an ASTNode as an argument and returns a VisitorResult.

        Returns:
            None
        """
        if function(self) == VisitorResult.CONTINUE:
            for child in self.get_children():
                child.accept(function)

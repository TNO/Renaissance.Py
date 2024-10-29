from abc import ABC, abstractmethod
from  enum import Enum
from pathlib import Path
from typing import Callable, Optional, TypeVar



# enum with ABORT, CONTINUE and SKIP
class VisitorResult(Enum):
    ABORT = 0
    CONTINUE = 1
    SKIP = 2

ASTNodeType = TypeVar("ASTNodeType", bound='ASTNode')

class ASTNode(ABC):
    def __init__(self, root: 'ASTNode') -> None:
        super().__init__()
        self.root = root
        self.cache = {}
    
    def isMatching(self, other: 'ASTNode') -> bool:
        return self.get_kind() == other.get_kind and self.get_properties() == other.get_properties()
        
    def is_part_of_translation_unit(self) -> bool:
        return self.get_containing_filename() == self.root.get_containing_filename()

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
        bytes = self.root._get_binary_file_content(self.get_containing_filename())
        return str(bytes[start:end], 'utf-8')

    def _get_binary_file_content(self, file_path):
        assert self is self.root,  "_getBinaryFileContent can only be used for the root node"
        try:
            return self.cache[file_path]
        except Exception as e:
            with open(file_path, 'rb') as f:
                bytes =  f.read()
                self.cache[file_path] = bytes
                return bytes

    @staticmethod
    @abstractmethod
    def load(file_path: Path)-> 'ASTNode':
        pass

    @staticmethod
    @abstractmethod
    def load_from_text(text: str, file_name: str) -> 'ASTNode':
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_containing_filename(self) -> str:
        pass
    
    @abstractmethod
    def get_start_offset(self) -> int: 
        pass

    @abstractmethod
    def get_length(self) -> int: 
        pass

    @abstractmethod
    def get_kind(self) -> str: 
        pass

    @abstractmethod
    def get_properties(self) -> dict[str, int|str]: 
        pass

    @abstractmethod
    def get_parent(self: ASTNodeType) -> Optional[ASTNodeType]: 
        pass

    @abstractmethod
    def is_statement(self) ->bool: 
        pass

    @abstractmethod
    def get_children(self: ASTNodeType) -> list[ASTNodeType]: 
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

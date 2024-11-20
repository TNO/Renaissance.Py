from pathlib import Path
from typing import Generic, Sequence, TypeVar

from .ast_node import ASTNodeType

class ASTFactory(Generic[ASTNodeType]):
    """
    A factory class for creating instances of ASTNodeType.
    Attributes:
        clazz (type[ASTNodeType]): The class type of the AST nodes to be created.
        extra_args (Sequence[str]): Additional arguments to be passed during the creation of AST nodes.
    """
    def __init__(self, clazz: type[ASTNodeType], extra_args:Sequence[str]=[]) -> None: 
        self.clazz = clazz
        self.extra_args = extra_args

    def create(self, file_path: Path)-> ASTNodeType:  
        atu = self.clazz.load(file_path=file_path, extra_args = self.extra_args)
        assert isinstance(atu, self.clazz), "The loaded AST node is not an instance of the expected type"
        return atu

    def create_from_text(self, text:str, file_name:str) -> ASTNodeType:  
        atu =  self.clazz.load_from_text(text, file_name, extra_args = self.extra_args)
        assert isinstance(atu, self.clazz), "The loaded AST node is not an instance of the expected type"
        return atu

if __name__ == "__main__":
    pass


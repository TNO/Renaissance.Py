from pathlib import Path
from typing import Sequence, TypeVar

from .ast_node import ASTNode

ASTNodeType = TypeVar("ASTNodeType", bound='ASTNode')

class ASTFactory:

    def __init__(self, clazz: type[ASTNodeType], extra_args:Sequence[str]=[]) -> None: 
        self.clazz = clazz
        self.extra_args = extra_args

    def create(self, file_path: Path):  
        return self.clazz.load(file_path=file_path, extra_args = self.extra_args)

    def create_from_text(self, text:str, file_name:str):  
        return self.clazz.load_from_text(text, file_name, extra_args = self.extra_args)

if __name__ == "__main__":
    pass


from pathlib import Path
from syntax_tree.ast_factory import ASTFactory

class TestModelLoader():

    @staticmethod
    def load_model(factory:ASTFactory):
        return  factory.create(Path(__file__).parent.parent.parent.parent / 'c/src/main.c')

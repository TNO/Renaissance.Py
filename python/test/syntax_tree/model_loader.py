from pathlib import Path
from syntax_tree.ast_factory import ASTFactory

class ModelLoader():

    @staticmethod
    def load_model(factory:ASTFactory):
        # note: make sure to load a corresponding model for the language
        return  factory.create(Path(__file__).parent.parent.parent.parent / 'c/src/main.c')


from pathlib import Path
from .ast_rewriter import ASTRewriter
from .ast_factory import ASTFactory

class ASTUtils:
    @staticmethod
    def commit(rewriter: ASTRewriter, factory: ASTFactory, in_memory: bool = False):
        rewriter.apply_to_string()
        if in_memory:
            atu = factory.create_from_text(rewriter.apply_to_string(), rewriter.get_filename())
            return atu, ASTRewriter(atu)
        else:
            #save file first then reload it
            with open(rewriter.get_filename(), 'wb') as f:
                f.write(rewriter.apply())
            atu = factory.create(Path(rewriter.get_filename()))
            return atu, ASTRewriter(atu)


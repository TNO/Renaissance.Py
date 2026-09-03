# use clang to load and walk a compilation database

from pathlib import Path

import targets
from renaissance.integrations.clang import ClangASTNode, CompilationDatabase
from renaissance.integrations.clang.clang_json_ast_node import ClangJsonASTNode
from renaissance.integrations.types import FunctionDef
from renaissance.syntax_tree import ASTProcessor, ASTShower


def main(args):
    # the first argument is the code to be parsed
    database = args[0] if len(args) > 0 else ""
    for impl_type in [ClangASTNode, ClangJsonASTNode]:
        # load the compilation database by specifying the path to the folder
        # and the implementation type
        db = CompilationDatabase.walk(impl_type, Path(database))
        for factory, atu in db:
            # show atu
            ASTShower.show_node(atu, include_properties=True)
            # do something with the factory and atu
            ast_refactor = ASTProcessor(atu, factory, in_memory=True)
            [print(n.text) for n in ast_refactor.find_ast_type(FunctionDef)]


if __name__ == "__main__":
    # fill in your own path
    main([targets.__file__.replace("__init__.py", "compile_commands.json")])

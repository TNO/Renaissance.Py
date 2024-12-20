
from pathlib import Path
from typing import Iterator
from syntax_tree import ASTNodeType, ASTFactory
from clang.cindex import CompilationDatabase as ClangCompilationDatabase

class CompilationDatabase:

    @staticmethod
    def walk(typ: type[ASTNodeType], path: Path) -> Iterator[tuple[ASTFactory, ASTNodeType]]:
        """
        Load the Clang compilation database and yield factory and AST node type tuples.

        Args:
            typ (type[ASTNodeType]): The type of AST node to be used.
            path (Path): The path to the directory containing the compilation database.

        Yields:
            Iterator[tuple[ASTFactory, ASTNodeType]]: An iterator of tuples, each containing
            an AST factory and an AST node type.

            Be careful to not use the Iterable is a list as it will load ALL the AST nodes in memory.
        """
        db = ClangCompilationDatabase.fromDirectory(str(path))
        def factory_and_atu(command):
            return CompilationDatabase.__create_processor(typ, command)
        yield from map(factory_and_atu, db.getAllCompileCommands())

    @staticmethod
    def __create_processor(typ: type[ASTNodeType], compile_command ) -> tuple[ASTFactory, ASTNodeType]:
        extra_args = list(compile_command.arguments)
        skip = ['-o', '-c']
        filtered_args = [arg for idx, arg in enumerate(extra_args) if arg != compile_command.filename 
                         and not arg in skip and (idx==0 or not extra_args[idx-1] in skip)]
        factory = ASTFactory(typ, extra_args=filtered_args, working_dir=Path(compile_command.directory))
        atu = factory.create(Path(compile_command.filename))  # The first argument is the file path
        return factory, atu
    
"""AI: Command-line entry point for running Python refactoring recipes on source files."""

import sys
from pathlib import Path

from renaissance.integrations.python.ast.extractor import PythonExtractor
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.project.project_scanner import PythonScanner
from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.syntax_tree import ASTShower

# TODO: is this file working as intended?
# See https://github.com/TNO/Renaissance.Py/issues/196


def refactor():
    """AI: Run the `refactor`/`extract`/`inspect` CLI subcommands based on `sys.argv`."""
    if sys.argv[1] == "refactor":
        refactoring = sys.argv[2]
        files = [sys.argv[3]] if len(sys.argv) > 3 else PythonScanner().find_sources()
        print(f"Refactor {Path().cwd()}")
        for file in files:
            PythonRefactoring.process(refactoring, file)

    if sys.argv[1] == "extract":
        print(f"Extracting {Path().cwd()}")
        extractor = PythonExtractor()
        for file in PythonScanner().find_sources():
            filename = sys.argv[2]
            extractor.process(file)
        extractor.save_graph(filename)
    if sys.argv[1] == "inspect":
        print(f"inspect {Path().cwd()}")
        file = sys.argv[2]
        ASTShower.focus = f"|{sys.argv[3]}"
        atu = PythonRstNode.load(Path(file))
        ASTShower.show_node(atu)


if __name__ == "__main__":
    refactor()

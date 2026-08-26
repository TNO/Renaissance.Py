import sys
from pathlib import Path

from renaissance.impl.python.extractor import PythonExtractor
from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.project.project_scanner import PythonScanner
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.syntax_tree import ASTShower


def refactor():
    if sys.argv[1] == "refactor":
        refactoring = sys.argv[2]
        files = [sys.argv[3]] if len(sys.argv) > 3 else PythonScanner().find_sources()
        print(f'Refactor {Path(".").resolve()}')
        for file in files:
            PythonRefactoring.process(refactoring, file)

    if sys.argv[1] == "extract":
        print(f'Extracting {Path(".").resolve()}')
        extractor = PythonExtractor()
        for file in PythonScanner().find_sources():
            filename = sys.argv[2]
            extractor.process(file)
        extractor.save_graph(filename)
    if sys.argv[1] == "inspect":
        print(f"inspect {Path('.').resolve()}")
        file = sys.argv[2]
        ASTShower.focus = f"|{sys.argv[3]}"
        atu = PythonRstNode.load(Path(file))
        ASTShower.show_node(atu)


if __name__ == "__main__":
    refactor()

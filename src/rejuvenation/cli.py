import sys
from pathlib import Path

from renaissance.impl.python import PythonRstNode
from renaissance.impl.python.extractor import PythonExtractor
from renaissance.project.project_scanner import PythonScanner
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.syntax_tree import ASTShower

if __name__ == "__main__":
    if sys.argv[1] == "refactor":
        print(f'Refactor {Path(".").resolve()}')
        for file in PythonScanner().find_sources():
            refactor = sys.argv[2]
            PythonRefactoring.process(refactor, file)

    if sys.argv[1] == "extract":
        print(f'Extracting {Path(".").resolve()}')
        extractor = PythonExtractor()
        for file in PythonScanner().find_sources():
            filename = sys.argv[2]
            extractor.process(file)
        extractor.save_graph(filename)
    if sys.argv[1] == "inspect":
        print(f"inspect {Path(".").resolve()}")
        file = sys.argv[2]
        ASTShower.focus = f"|{sys.argv[3]}"
        atu = PythonRstNode.load(Path(file))
        ASTShower.show_node(atu)
